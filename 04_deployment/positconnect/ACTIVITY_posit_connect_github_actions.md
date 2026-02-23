# 📌 ACTIVITY

## Deploy to Posit Connect via GitHub Actions

🕒 *Estimated Time: 10-15 minutes*

---

## ✅ Your Task

In this activity, you will set up **GitHub Actions** to automatically deploy your applications to **Posit Connect** when you push code to your repository.

### 🧱 Stage 1: Create Posit Connect API Key

- [ ] An email from connect.systems-apps.com has been sent to you, inviting you to join our Posit Connect server. Please accept the invite. (It probably went to your Spam Folder!)
- [ ] Navigate to Your Account's **Manage Your API Keys** page.
![](../../docs/images/pc_keys_where.png)
- [ ] Navigate to API Keys and select **"+ New API Key"**.
![](../../docs/images/pc_keys_view.png)
- [ ] Create a new API Key. Give it **Publisher** level access, a logical name, and click **Create Key**.
![](../../docs/images/pc_keys_new.png)
- [ ] Copy your new API Key and store it somewhere safe. You will only ever see it one time. If you miss it, you'll need to create a new API key.
![](../../docs/images/pc_keys_copy.png)

<br>
---

### 🧱 Stage 2: Set Up GitHub Secrets

You need to configure two secrets in your GitHub repository for **Posit Connect** deployment:

- [ ] Go to your GitHub repository and navigate to **Settings** → **Secrets and variables** → **Actions**
![](../../docs/images/pc_github_settings.png)
- [ ] Click **New repository secret**
![](../../docs/images/pc_github_secrets.png)
- [ ] Create a secret named `CONNECT_SERVER` with the value `https://connect.systems-apps.com`
![](../../docs/images/pc_github_secrets_CONNECT_SERVER.png)
- [ ] Create another secret named `CONNECT_API_KEY` with your **Publisher API key** from Posit Connect. 
  - (Remember: To get your API key: Log into `connect.systems-apps.com`, go to your account settings, and create a new **Publisher** API key)
- [ ] At the end, your keys list should look something like this. (I have multiple Repository Secrets; you will have just 2.)
![](../../docs/images/pc_keys_list.png)

<br>
---

### 🧱 Stage 3: Create GitHub Actions Workflow

Next, we need to create a **Github Actions workflow file** to deploy your application via Github. (There are other ways to deploy to Posit Connect, but this is the only easy way to sync it with your individual <u>private</u> **Github Repo**.)
At the following links are several workflow templates, each designed to match a specific type of app. 

Choose from:

- For Shiny R Apps, use [`.github/workflows/deploy-shinyr.yml`](../../.github/workflows/deploy-shinyr.yml).
- For Shiny Python Apps, use [`.github/workflows/deploy-shinypy.yml`](../../.github/workflows/deploy-shinypy.yml).
- For R-based Plumber APIs, use [`github/workflows/deploy-plumber.yml`](../../.github/workflows/deploy-plumber.yml).
- For Python-based FastAPI apps, use [`.github/workflows/deploy-fastapi.yml`](../../.github/workflows/deploy-fastapi.yml).

- [ ] Please select the appropriate template, copy it, and put it in a file at this path in  your repo: `.github/workflows/<NAME_OF_YOUR_FILE>.yml`. 
- Note: It **must** go in the `.github/workflows` folder; this is a reserved name for Github actions.
- [ ] Adjust the `paths` section to match your repository structure.
  - For example, to adjust this Shiny Python app's yml, you could...
  ![](../../docs/images/pc_deploy_shinypy.png)
     - [ ] Update paths in **Lines 7-8**, which say **if these files change, go redeploy the app**.
     - [ ] Update path in `dir` argument on **Line 29**.
- [ ] Commit and push the workflow file to your repository

<br>
---

### 🧱 Stage 3: Test Deployment

- [ ] Push your changes to the `main` branch (or trigger the workflow manually via **Actions** → **Deploy [Your App] to Posit Connect** → **Run workflow**)
- [ ] Check the **Actions** tab in your GitHub repository to see the workflow running. 
   - In the example below, we deployed 4 separate apps via 4 `.yaml` docs. 2 actions succeeded (shinyr and plumber) and 2 actions failed (shinypy and fastapi). 
![](../../docs/images/pc_actions_list.png)
- [ ] Once the workflow completes successfully, log into `connect.systems-apps.com` and verify your application appears in the dashboard
- [ ] Click on your deployed application to test it

---

# 📤 To Submit

- For credit: Submit a screenshot showing your successfully deployed application on **Posit Connect** (the application dashboard view)

---

![](../../docs/images/icons.png)

---

← 🏠 [Back to Top](#ACTIVITY)
