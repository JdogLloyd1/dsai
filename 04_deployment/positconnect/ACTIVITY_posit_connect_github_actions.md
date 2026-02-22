# 📌 ACTIVITY

## Deploy to Posit Connect via GitHub Actions

🕒 *Estimated Time: 10-15 minutes*

---

## ✅ Your Task

In this activity, you will set up **GitHub Actions** to automatically deploy your applications to **Posit Connect** when you push code to your repository.

### 🧱 Stage 1: Set Up GitHub Secrets

You need to configure two secrets in your GitHub repository for **Posit Connect** deployment:

- [ ] Go to your GitHub repository and navigate to **Settings** → **Secrets and variables** → **Actions**
- [ ] Click **New repository secret**
- [ ] Create a secret named `CONNECT_SERVER` with the value `https://connect.systems-apps.com`
- [ ] Create another secret named `CONNECT_API_KEY` with your **Publisher API key** from Posit Connect
  - To get your API key: Log into `connect.systems-apps.com`, go to your account settings, and create a new **Publisher** API key

### 🧱 Stage 2: Create GitHub Actions Workflow

Create a GitHub Actions workflow file to deploy your application. Choose the workflow template that matches your app type:

#### For Shiny R Apps

Create `.github/workflows/deploy-shinyr.yml`:

```yaml
name: Deploy Shiny R App to Posit Connect

on:
  push:
    branches: [main]
    paths:
      - '04_deployment/positconnect/shinyr/**'
      - '.github/workflows/deploy-shinyr.yml'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up R
        uses: r-lib/actions/setup-r@v2
        with:
          r-version: '4.5.2'
          use-public-rspm: true

      - name: Publish to Posit Connect
        uses: rstudio/actions/connect-publish@main
        with:
          url: ${{ secrets.CONNECT_SERVER }}
          api-key: ${{ secrets.CONNECT_API_KEY }}
          access-type: acl
          dir: 04_deployment/positconnect/shinyr
          force: false
```

#### For Shiny Python Apps

Create `.github/workflows/deploy-shinypy.yml`:

```yaml
name: Deploy Shiny Python App to Posit Connect

on:
  push:
    branches: [main]
    paths:
      - '04_deployment/positconnect/shinypy/**'
      - '.github/workflows/deploy-shinypy.yml'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Publish to Posit Connect
        uses: rstudio/actions/connect-publish@main
        with:
          url: ${{ secrets.CONNECT_SERVER }}
          api-key: ${{ secrets.CONNECT_API_KEY }}
          access-type: acl
          dir: 04_deployment/positconnect/shinypy
          force: false
```

#### For Plumber API

Create `.github/workflows/deploy-plumber.yml`:

```yaml
name: Deploy Plumber API to Posit Connect

on:
  push:
    branches: [main]
    paths:
      - '04_deployment/positconnect/plumber/**'
      - '.github/workflows/deploy-plumber.yml'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up R
        uses: r-lib/actions/setup-r@v2
        with:
          r-version: '4.5.2'
          use-public-rspm: true

      - name: Publish to Posit Connect
        uses: rstudio/actions/connect-publish@main
        with:
          url: ${{ secrets.CONNECT_SERVER }}
          api-key: ${{ secrets.CONNECT_API_KEY }}
          access-type: acl
          dir: 04_deployment/positconnect/plumber
          force: false
```

#### For FastAPI

Create `.github/workflows/deploy-fastapi.yml`:

```yaml
name: Deploy FastAPI to Posit Connect

on:
  push:
    branches: [main]
    paths:
      - '04_deployment/positconnect/fastapi/**'
      - '.github/workflows/deploy-fastapi.yml'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Publish to Posit Connect
        uses: rstudio/actions/connect-publish@main
        with:
          url: ${{ secrets.CONNECT_SERVER }}
          api-key: ${{ secrets.CONNECT_API_KEY }}
          access-type: acl
          dir: 04_deployment/positconnect/fastapi
          force: false
```

- [ ] Create the appropriate workflow file for your app type in `.github/workflows/` directory
- [ ] Adjust the `paths` section to match your repository structure if needed
- [ ] Commit and push the workflow file to your repository

### 🧱 Stage 3: Test Deployment

- [ ] Push your changes to the `main` branch (or trigger the workflow manually via **Actions** → **Deploy [Your App] to Posit Connect** → **Run workflow**)
- [ ] Check the **Actions** tab in your GitHub repository to see the workflow running
- [ ] Once the workflow completes successfully, log into `connect.systems-apps.com` and verify your application appears in the dashboard
- [ ] Click on your deployed application to test it

---

# 📤 To Submit

- For credit: Submit a screenshot showing your successfully deployed application on **Posit Connect** (the application dashboard view)

---

![](../../docs/images/icons.png)

---

← 🏠 [Back to Top](#ACTIVITY)
