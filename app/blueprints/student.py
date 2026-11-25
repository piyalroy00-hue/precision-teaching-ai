from flask import Blueprint, redirect, render_template, request, session

from app.database.db import get_session
from app.ai.tutor import TutorContext
from app.models import AIMessage, AISession, GeneratedContent, LearningResource, LearningSession, MasterySnapshot, Question, Response, Subject, Topic
from app.services.adaptive_assessment_service import (
    choose_adaptive_question,
    current_adaptive_difficulty,
    start_adaptive_assessment,
    submit_adaptive_response,
)
from app.services.assessment_service import (
    complete_assessment,
    get_fixed_diagnostic_questions,
    start_assessment,
    submit_response,
)
from app.services.knowledge_service import classify_concepts, get_topic_mastery_report
from app.services.learning_service import complete_learning_session, get_or_start_learning_session
from app.services.recommendation_service import build_learning_path
from app.services.generated_practice_service import generate_practice_question, get_or_create_generated_practice
from app.services.personalized_tutor_service import PersonalizedTutorService
from app.services.tutor_conversation_service import respond_to_student, start_ai_session

bp = Blueprint("student", __name__)


@bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    student_id = session["user_id"]
    with get_session() as db_session:
        from app.models import Response

        responses = db_session.query(Response).filter_by(student_id=student_id).all()
        total_attempted = len(responses)
        total_correct = sum(1 for r in responses if r.is_correct)
        total_score = sum(r.score for r in responses)
        mastery_report = get_topic_mastery_report(db_session, student_id)
        concepts = classify_concepts(db_session, student_id)

    accuracy = (total_correct / total_attempted * 100) if total_attempted else 0.0
    return render_template(
        "student/dashboard.html",
        user_name=session["user_name"],
        student_code=session["user_student_code"],
        total_attempted=total_attempted,
        accuracy=accuracy,
        total_score=total_score,
        mastery_report=mastery_report,
        concepts=concepts,
    )


@bp.route("/assessment", methods=["GET", "POST"])
def assessment():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        action = request.form.get("action")

        if action == "start":
            if session.get("assessment_id"):
                return redirect("/assessment")
            with get_session() as db_session:
                subject = db_session.query(Subject).filter_by(name="Python Programming").one()
                questions = get_fixed_diagnostic_questions(db_session, subject.id)
                assessment = start_assessment(db_session, session["user_id"], subject.id)
            session["assessment_id"] = assessment.id
            session["question_ids"] = [q.id for q in questions]
            session["question_index"] = 0
            return redirect("/assessment")

        if action == "submit":
            assessment_id = session.get("assessment_id")
            question_ids = session.get("question_ids", [])
            question_index = int(session.get("question_index", 0))
            if assessment_id is None or not question_ids:
                return redirect("/assessment")
            if question_index >= len(question_ids):
                return redirect("/assessment")

            question_id = question_ids[question_index]
            answer = request.form.get("answer", "").strip()
            if not answer:
                return render_template("student/assessment.html", error="Please select an answer before submitting.")

            with get_session() as db_session:
                submit_response(
                    db_session,
                    assessment_id,
                    session["user_id"],
                    question_id,
                    answer=answer,
                    time_taken=0.0,
                )
            session["question_index"] = question_index + 1
            return redirect("/assessment")

    assessment_id = session.get("assessment_id")
    question_ids = session.get("question_ids", [])
    question_index = int(session.get("question_index", 0))

    if not assessment_id:
        return render_template("student/assessment.html", ready=False)

    if question_index >= len(question_ids):
        with get_session() as db_session:
            planned_questions = [db_session.get(Question, question_id) for question_id in question_ids]
            total_possible = sum(question.marks for question in planned_questions if question is not None)
            assessment = complete_assessment(db_session, assessment_id, total_possible=total_possible)
            total_score = assessment.total_score
            percentage = assessment.percentage
        session.pop("assessment_id", None)
        session.pop("question_ids", None)
        session.pop("question_index", None)
        return render_template(
            "student/assessment.html",
            ready=False,
            completed=True,
            total_score=total_score,
            total_possible=total_possible,
            percentage=percentage,
        )

    with get_session() as db_session:
        question = db_session.get(Question, question_ids[question_index])
        options = [opt.option_text for opt in question.options]
        question_topic = question.topic.name
        question_difficulty = question.difficulty
        question_text = question.question_text

    return render_template(
        "student/assessment.html",
        ready=True,
        question_index=question_index,
        total_questions=len(question_ids),
        question_topic=question_topic,
        question_difficulty=question_difficulty,
        question_text=question_text,
        options=options,
    )


@bp.route("/learning-plan")
def learning_plan():
    if "user_id" not in session:
        return redirect("/")
    with get_session() as db_session:
        plan = build_learning_path(db_session, session["user_id"])
    return render_template("student/learning_plan.html", plan=plan)


@bp.route("/progress")
def progress():
    if "user_id" not in session:
        return redirect("/")
    with get_session() as db_session:
        responses = db_session.query(Response).filter_by(student_id=session["user_id"]).all()
        sessions = db_session.query(LearningSession).filter_by(student_id=session["user_id"]).all()
        snapshots = (
            db_session.query(MasterySnapshot)
            .filter_by(student_id=session["user_id"])
            .order_by(MasterySnapshot.recorded_at.desc())
            .limit(20)
            .all()
        )
        progress_rows = [
            {"topic": snapshot.topic.name, "mastery": snapshot.mastery_probability,
             "recorded_at": snapshot.recorded_at.strftime("%Y-%m-%d %H:%M")}
            for snapshot in snapshots
        ]
        difficulty_counts = {
            difficulty: sum(1 for response in responses if response.question.difficulty == difficulty)
            for difficulty in ("Easy", "Medium", "Hard")
        }
        completed_sessions = sum(1 for learning_session in sessions if learning_session.completed_at)
        learning_minutes = sum(
            learning_session.resource.estimated_minutes
            for learning_session in sessions
            if learning_session.completed_at
        )
    return render_template(
        "student/progress.html", progress_rows=progress_rows, attempts=len(responses),
        learning_minutes=learning_minutes,
        completed_sessions=completed_sessions, total_sessions=len(sessions), difficulty_counts=difficulty_counts,
    )


def _tutor_context(db_session, student_id: int, topic: Topic) -> TutorContext:
    report = get_topic_mastery_report(db_session, student_id)
    mastery_item = next((item for item in report if item["topic_id"] == topic.id), None)
    mastery = mastery_item["mastery_probability"] if mastery_item else 0.20
    mastery_level = mastery_item["mastery_level"] if mastery_item else "Beginner"
    difficulty = "Easy" if mastery < 0.40 else "Medium" if mastery < 0.80 else "Hard"
    errors = [
        response.question.question_text
        for response in (
            db_session.query(Response)
            .filter_by(student_id=student_id)
            .order_by(Response.submitted_at.asc())
            .all()
        )
        if not response.is_correct and response.question.topic_id == topic.id
    ][-2:]
    return TutorContext(
        subject="Python Programming", topic=topic.name, subtopic=None,
        mastery_probability=mastery, mastery_level=mastery_level, difficulty=difficulty,
        learning_objective=f"Apply {topic.name} accurately in a Python program.",
        previous_errors=tuple(errors), learning_session_id=session.get("learning_session_id"),
    )


@bp.route("/tutor", methods=["GET", "POST"])
def tutor():
    if "user_id" not in session:
        return redirect("/")
    with get_session() as db_session:
        topic_id = request.values.get("topic_id", type=int) or session.get("adaptive_topic_id")
        topic = db_session.get(Topic, topic_id) if topic_id else db_session.query(Topic).order_by(Topic.id).first()
        if topic is None:
            return redirect("/learning-plan")
        context = _tutor_context(db_session, session["user_id"], topic)
        ai_session_id = session.get("ai_session_id")
        if not ai_session_id or session.get("ai_topic_id") != topic.id:
            ai_session = start_ai_session(db_session, session["user_id"], topic.id)
            ai_session_id = ai_session.id
            session["ai_session_id"] = ai_session_id
            session["ai_topic_id"] = topic.id
        if request.method == "POST":
            user_question = request.form.get("question", "")
            respond_to_student(db_session, ai_session_id, context, user_question)
            return redirect(f"/tutor?topic_id={topic.id}")
        instruction = PersonalizedTutorService().generate(context)
        practice = generate_practice_question(context)
        get_or_create_generated_practice(db_session, session["user_id"], topic.id, practice)
        messages = db_session.query(AIMessage).filter_by(session_id=ai_session_id).order_by(AIMessage.timestamp).all()
        message_data = [{"role": message.role, "message": message.message} for message in messages]
        tutor_data = {"topic": topic.name, "instruction": instruction, "practice": practice}
    return render_template("student/tutor.html", tutor=tutor_data, messages=message_data)


@bp.route("/learning/<int:resource_id>", methods=["GET", "POST"])
def learning(resource_id: int):
    if "user_id" not in session:
        return redirect("/")
    if request.method == "POST":
        learning_session_id = int(request.form["learning_session_id"])
        with get_session() as db_session:
            learning_session = complete_learning_session(
                db_session,
                learning_session_id,
                session["user_id"],
                expected_resource_id=resource_id,
            )
            session["adaptive_topic_id"] = learning_session.topic_id
        return redirect("/adaptive-practice")

    with get_session() as db_session:
        resource = db_session.get(LearningResource, resource_id)
        if resource is None:
            return redirect("/learning-plan")
        learning_session = get_or_start_learning_session(db_session, session["user_id"], resource.id)
        resource_data = {
            "title": resource.title,
            "content": resource.content,
            "resource_type": resource.resource_type,
            "estimated_minutes": resource.estimated_minutes,
            "topic": resource.topic.name,
        }
    return render_template("student/learning.html", resource=resource_data, learning_session_id=learning_session.id)


@bp.route("/adaptive-practice", methods=["GET", "POST"])
def adaptive_practice():
    if "user_id" not in session:
        return redirect("/")
    topic_id = session.get("adaptive_topic_id")
    if topic_id is None:
        return redirect("/learning-plan")

    if request.method == "POST":
        if "adaptive_assessment_id" not in session:
            return redirect("/adaptive-practice")
        question_id = int(request.form["question_id"])
        answer = request.form.get("answer", "").strip()
        if not answer:
            return redirect("/adaptive-practice")
        with get_session() as db_session:
            response, previous, updated, next_difficulty = submit_adaptive_response(
                db_session,
                session["adaptive_assessment_id"],
                session["user_id"],
                question_id,
                answer,
                expected_topic_id=topic_id,
            )
        session["adaptive_feedback"] = {
            "correct": response.is_correct,
            "previous": previous,
            "updated": updated,
            "next_difficulty": next_difficulty,
        }
        return redirect("/adaptive-practice")

    with get_session() as db_session:
        topic = db_session.get(Topic, topic_id)
        if topic is None:
            return redirect("/learning-plan")
        if "adaptive_assessment_id" not in session:
            assessment = start_adaptive_assessment(db_session, session["user_id"], topic.subject_id)
            session["adaptive_assessment_id"] = assessment.id
        difficulty = current_adaptive_difficulty(db_session, session["user_id"], topic.id)
        question = choose_adaptive_question(db_session, session["user_id"], topic.id, difficulty)
        state = get_topic_mastery_report(db_session, session["user_id"])
        mastery = next((item["mastery_probability"] for item in state if item["topic_id"] == topic.id), 0.20)
        question_data = None if question is None else {
            "id": question.id,
            "text": question.question_text,
            "options": [option.option_text for option in question.options],
        }
        topic_name = topic.name
    feedback = session.pop("adaptive_feedback", None)
    return render_template(
        "student/adaptive_practice.html", topic_name=topic_name, mastery=mastery,
        difficulty=difficulty, question=question_data, feedback=feedback,
    )
