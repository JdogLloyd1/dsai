# `dsai` - Data Science and AI for Systems Engineering

*Course repository for SYSEN 5381: Data Science and AI for Systems Engineering*

> This repository contains code and exercises for the course Data Science and AI for Systems Engineering, henceforth **DSAI**. Students will build skils for modern AI applications using APIs and Apps.

> You may use Python, R, or another language/framework of your choosing. Lessons and starter code are provided in R and/or Python. You may even mix and match at times, writing an API in Python and an App in R, etc.

---

![](images/banner.png)
---

## COURSE DESCRIPTION

Modern engineering systems increasingly rely on cloud-based, AI-driven data processing, automation, and analytics. This course equips Systems Engineering students with the coding skills needed to interact with cloud-hosted data, automate workflows, and build scalable AI-powered apps and analytics. Students will gain hands-on experience in querying web APIs, building APIs, and leveraging AI models for automation. Topics include API calls, querying Generative AI, and automation, all to serve automated data reporting. Participants will learn to examine and critique uses of AI in modern systems, considering risk, value, tradeoffs, and policy issues for the customer and society. By the end of the course, students will have built cloud-hosted, AI-powered applications and reporting systems that can dynamically retrieve, process, and visualize data using generative AI.

Students are expected to spend 3-4 hours per week per credit hour. Intended for graduate students performing technical tasks interested in software development or data analytics.

## COURSE LEARNING OUTCOMES

By the end of this course, participants will be able to:

1. **Design data pipelines** that interact with public and private APIs to retrieve, process, and analyze structured data for engineering applications.
2. **Build REST APIs** to automate data analytics and AI operations.
3. **Build AI-powered applications** using queries to generative AI models and prompt engineering.

## COURSE FORMAT

- Reverse-classroom hybrid format, with on-campus and distance learning sections. 
- 3 classes per week total, including 1 class of instructional activities and 2 classes of coding ‘lab’ activities, plus online tutorials.

Students are assigned lectures, demos, and readings each week to learn new techniques. Then, classes are structured as ‘lab hours’ where they practice and implement their techniques,  giving students a mix of group learning and one-on-one time with the professor. Students are expected to come to Lab Hours having read the material for the week, ready to apply.

---

## SHOULD I TAKE THIS COURSE?

### WHO IS THIS COURSE FOR?

Do any of the following apply to you? If so, this course may be a great fit for your professional goals:

- [ ] **Systems engineers** who want to build **cloud data pipelines** and automate workflows using APIs.
- [ ] **Engineers and analysts** looking to improve their **AI and API interaction skills**.
- [ ] **Engineers** working with **real-time and large-scale data** who need to integrate, process, and report findings from cloud-based data sources.
- [ ] **Professionals looking to build AI-driven applications** using APIs for chatbot development and intelligent reporting.
- [ ] **Analysts and data scientists** seeking to create **reproducible, automated reports** with RMarkdown and API-driven dashboards.
- [ ] **Learners** who want **hands-on experience in using LLMs** without needing prior AI infrastructure expertise.

This course is ideal for those who want to level up their technical skills in data engineering, automation, and AI-powered analytics.

### WHY THIS COURSE?

Cloud databases, APIs, and AI-driven automation are rapidly transforming how engineers access, process, and report data. However, integrating these technologies into company workflows requires training and expertise. This course promotes fluency in cloud-based data analytics by focusing on **3 key skills** relevant to modern systems engineers: (1) **Interacting with APIs**; (2) **Automating AI-driven data processing**; and (3) **Building reproducible, automated reporting systems**. By the end of the course, students will not only understand  data engineering but also build and deploy applications that leverage APIs, AI, and scalable computing.

### WHAT MAKES THIS COURSE UNIQUE?

This course addresses a critical skills gap in modern engineering education by providing hands-on experience with cloud computing, API development, and AI integration. The reverse-classroom format allows students to learn at their own pace while maximizing hands-on lab time for practical application. The course will provide students with marketable skills in high-demand areas of data engineering and AI automation.

This course is distinct from existing data science courses in that it focuses specifically on data engineering, API development, and AI integration rather than general data analysis. It complements existing courses by providing practical skills for building and deploying AI-powered apps.

Additionally, this course includes critical thinking and reviews of AI applications from a broader policy and risk perspective. Drawing from key texts in computational social science, this course helps students make specific choices when architecting their system that maximizes the utility of their APIs and AI tools while minimizing societal risk.

---


## Weekly Topics

### PART 1: DATA SCIENCE FOR AI

- **Module 0: Data Science Quickstart**
  - Installing Github
  - Installing R
  - Installing Python
  - Installing Cursor
  - Using GitHub
  - Using Cursor
  - Using Git Bash
  - Helpful Functions and where to find them

- **Module 1: API Queries**
  - API Calls and the Hyper Text Transfer Protocol (HTTP)
  - Making API Calls: GET, POST, and more
  - API Security: Authentification
  - Iterating API Calls
  - Case: US Census
  - Case: PurpleAir
  - Case: SafeCast
  - ***LAB: Query An API***

- **Module 2: AI API Calls**
  - Using Ollama server
  - Downloading your first AI model
  - Serving your first AI model 
  - Querying your first AI model
  - Making your first AI Reporter with RMarkdown
  - ***LAB: Build an AI-Powered Reporter***


- **Module 3: Prompt Engineering**
  - Prompt Engineering for AI Models
  - Structuring Outputs as JSON
  - Structuring Prompts as XML
  - Iterating AI Queries
  - ***LAB: Validate 2+ AI Prompts***

---

### PART 2: AGENTS FOR AI

- **Module: Agents**
  - LangChain with Reticulate
  - 2-agent AI
  - Agent Rules
  - Diagrams/Architecture for Agentic AI
  - ***LAB: AI Reporter with Multi-Agent Editor***

- **Module: Function Calling with AI**
  - What's a REST API
  - Writing Endpoints
  - Function Calling with ellmer
  - Function Calling an external API
  - Function Calling with your local REST API
  - ***LAB: AI Reporter with Function Calling***
  - READINGS:
    - [Tool Calling with LangChain}](https://python.langchain.com/docs/concepts/tool_calling/)


- **Module 07: Retrieval Augmented Generation**
  - What is RAG? Why does it work?
  - RAG with String Searches
  - RAG with SQLite Databases
  - RAG with NLP
  - ***LAB: AI Reporter with RAG***

---

### PART 3: AI FOR DATA SCIENCE

- **Module: AI for Text Analysis**
  - Intro to Text Analysis
  - Qualitative Content Analysis
  - Content Analysis with AI
  - **LAB: TBD**

- **Module: AI for Data Management**
  - Intro to Database Types and Schemas
  - AI for Standardizing Inputs
  - Case: Managing Address Data
  - Case: Creating Database Entries
  - Case: Database Security with AI / Handling Code Injection

- **Module: AI for Decision-Making**
  - AI Prompting for Insights
  - Case: Emissions Reporter
  - AI Prompting for Decision-Making
  - Case: Recidivism
  - AI Prompting for Pattern Recognition
  - Case: Health Care Charts
  - AI Alternatives to Optimization

- **Module: Multi-Service Systems**
  - Integrating Predictive Models into Endpoints
  - AI + Statistical Modeling


### FURTHER READInG

- Module: Containers
  - Installing Docker 
  - What's a Docker Image? 
  - Pulling Docker Images for Course 
  - Starting and Stopping Containers 
  - Mounting Folders
  - Querying a Containerized API
  - Docker Compose
  - Setting up an AI system with Containers



---

# 🚨 Requirements

| Requirement | Type | Notes |
|-------------|------|-------|
| A PC, Mac, or Linux computer | Required | For running code |
| Basic knowledge of R or Python | Required | Core programming skills |
| Google account for Google Sheets access | Required | For database exercises |
| GitHub account, local dev environment | Required | For version control and development |

---

# 💬 Questions?

Reach out via Canvas or use EdDiscussion. You're not expected to know everything upfront — the point is to **try**, **fail**, **fix**, and **learn**!

---
