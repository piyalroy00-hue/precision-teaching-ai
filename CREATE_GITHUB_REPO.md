╔════════════════════════════════════════════════════════════════════════════════╗
║                 HOW TO CREATE A GITHUB REPOSITORY                             ║
║                     (5 minutes to complete)                                   ║
╚════════════════════════════════════════════════════════════════════════════════╝

STEP 1: CREATE GITHUB ACCOUNT (if you don't have one)
════════════════════════════════════════════════════════════════════════════════

1. Go to https://github.com
2. Click "Sign up"
3. Enter your email and create a password
4. Verify your email
5. Complete profile setup

STEP 2: CREATE A NEW REPOSITORY ON GITHUB
════════════════════════════════════════════════════════════════════════════════

1. Go to https://github.com/new
2. OR click the "+" icon in top right → "New repository"

3. Fill in the form:
   ┌─────────────────────────────────────────────────────────┐
   │ Repository name: precision-teaching-ai                  │
   │ Description:     AI-Based Adaptive Teaching System       │
   │ Visibility:      Public (or Private if you prefer)       │
   │ Initialize repo: DO NOT check any boxes                  │
   │                  (we're pushing existing code)           │
   └─────────────────────────────────────────────────────────┘

4. Click "Create repository"

5. You'll see a page with instructions. It will show:
   - Your repository URL (looks like: https://github.com/YOUR_USERNAME/precision-teaching-ai)
   - Commands to push existing code

STEP 3: CREATE A PERSONAL ACCESS TOKEN
════════════════════════════════════════════════════════════════════════════════

You need a Personal Access Token to authenticate with HTTPS:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Fill in:
   - Token name: "precision-teaching-deploy"
   - Expiration: 90 days (or longer)
   - Scopes: Check "repo" (full control of private repositories)
4. Click "Generate token"
5. ⚠️ COPY THE TOKEN IMMEDIATELY (you won't see it again!)
   - Keep it safe and secure
   - DO NOT share it
   - DO NOT commit it to git

STEP 4: PUSH YOUR CODE TO GITHUB
════════════════════════════════════════════════════════════════════════════════

After creating the repository and token, run these commands in PowerShell:

   cd "C:\Users\BRAINWARE UNIVERSITY\Desktop\SMR Project"
   
   git remote add origin https://github.com/YOUR_USERNAME/precision-teaching-ai.git
   
   git branch -M main
   
   git push -u origin main

Replace "YOUR_USERNAME" with your actual GitHub username!

When prompted for authentication:
   - Username: Your GitHub username
   - Password: Paste your Personal Access Token (not your GitHub password!)

STEP 5: VERIFY ON GITHUB
════════════════════════════════════════════════════════════════════════════════

1. Go to your repository: https://github.com/YOUR_USERNAME/precision-teaching-ai
2. You should see all your files there
3. If you see the deployment files (Procfile, render.yaml, etc.), it worked! ✅

════════════════════════════════════════════════════════════════════════════════
                            SUMMARY OF ACTIONS
════════════════════════════════════════════════════════════════════════════════

✓ Create GitHub account (if needed)
✓ Create new repository on GitHub
✓ Create Personal Access Token
✓ Run git commands to push code
✓ Verify files appear on GitHub

════════════════════════════════════════════════════════════════════════════════
                           USEFUL LINKS
════════════════════════════════════════════════════════════════════════════════

Create new repository:       https://github.com/new
Personal Access Tokens:      https://github.com/settings/tokens
GitHub Documentation:        https://docs.github.com/
SSH Setup (alternative):     https://docs.github.com/en/authentication/connecting-to-github-with-ssh

════════════════════════════════════════════════════════════════════════════════
                         TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════════

"fatal: 'origin' does not appear to be a 'git' repository"
  → Run: git remote add origin https://github.com/YOUR_USERNAME/precision-teaching-ai.git

"Authentication failed"
  → Make sure you're using the Personal Access Token, not your password
  → Token should be copied exactly as shown (no extra spaces)

"Pushing to wrong repository"
  → Check: git remote -v
  → Update: git remote set-url origin https://github.com/YOUR_USERNAME/precision-teaching-ai.git

════════════════════════════════════════════════════════════════════════════════

After completing these steps, run the remaining push commands and proceed to Step 2 (Render deployment)!
