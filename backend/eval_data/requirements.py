"""16 project requirements with hand-assigned relevance labels.

``relevant`` maps employee name -> grade:
    2 = strong match (has the core skills, described in this or similar words)
    1 = partial match (adjacent or supporting skills)
Anyone not listed counts as not relevant (grade 0).

``filters`` are structured constraints a manager might set. The labels already
take the filters into account: an employee who would be relevant but does not
pass the filter (for example an UNAVAILABLE person when only AVAILABLE people
are wanted) is deliberately left out of ``relevant``.

These labels were written by the project team from the persona definitions;
they are a small hand-made benchmark, not ground truth from a real company.
"""

AVAILABLE_ONLY = {"availability": ["AVAILABLE"]}
CAN_START = {"availability": ["AVAILABLE", "PARTIALLY_AVAILABLE"]}

REQUIREMENTS: list[dict] = [
    {"id": "R01", "filters": {},
     "text": "We are moving our payment services onto a container orchestration platform. We need engineers who have run production workloads on clusters and manage infrastructure as code.",
     "relevant": {"Rohit Sethi": 2, "Meenal Arora": 2, "Shruti Pillai": 2, "Tarun Bedi": 1}},
    {"id": "R02", "filters": {},
     "text": "Looking for people who can manage pods, deployments, autoscaling and Helm charts on EKS or GKE.",
     "relevant": {"Rohit Sethi": 2, "Meenal Arora": 2, "Shruti Pillai": 1}},
    {"id": "R03", "filters": {},
     "text": "Build an assistant that answers employee questions from our policy documents using large language models and retrieval, with answers linked to their source.",
     "relevant": {"Pranav Iyer": 2, "Ishani Rao": 1}},
    {"id": "R04", "filters": {},
     "text": "Real-time visual inspection that detects defects on a production line and runs on small edge devices.",
     "relevant": {"Kartik Malhotra": 2, "Priyanka Dutta": 1}},
    {"id": "R05", "filters": AVAILABLE_ONLY,
     "text": "High-throughput event-driven backend services that process thousands of messages per second.",
     "relevant": {"Harsh Vora": 2, "Aryan Luthra": 1}},
    {"id": "R06", "filters": {},
     "text": "Customer-facing React web application with an accessible, consistent component library.",
     "relevant": {"Zoya Khan": 2, "Jatin Wadhwa": 1, "Naina Kohli": 1}},
    {"id": "R07", "filters": {},
     "text": "Design and build ETL pipelines and a data warehouse for our transactional data.",
     "relevant": {"Rajat Menon": 2, "Pallavi Nair": 1}},
    {"id": "R08", "filters": {},
     "text": "Create executive dashboards and KPI reports for revenue and churn.",
     "relevant": {"Pallavi Nair": 2, "Sonal Dixit": 1}},
    {"id": "R09", "filters": {},
     "text": "Cross-platform mobile app for field technicians that keeps working without network.",
     "relevant": {"Ruchi Saxena": 2, "Vedant Kulkarni": 1}},
    {"id": "R10", "filters": {},
     "text": "Security review of our cloud accounts: find weaknesses, review access policies and recommend fixes.",
     "relevant": {"Gautam Anand": 2, "Rohit Sethi": 1}},
    {"id": "R11", "filters": {},
     "text": "Automated regression testing for a web application, running in the CI pipeline on every pull request.",
     "relevant": {"Anirudh Kapoor": 2, "Tanvi Bajaj": 1, "Tarun Bedi": 1}},
    {"id": "R12", "filters": CAN_START,
     "text": "Predict product demand for a retail client so they can plan stock levels.",
     "relevant": {"Sonal Dixit": 2, "Rajat Menon": 1}},
    {"id": "R13", "filters": {},
     "text": "A delivery lead to run Agile sprints, manage risks and keep a multi-team product launch on schedule.",
     "relevant": {"Kritika Oberoi": 2, "Manoj Rawat": 1}},
    {"id": "R14", "filters": {},
     "text": "Our database queries are slow and we need replication and a tested recovery plan.",
     "relevant": {"Chetan Bhargava": 2, "Debina Sen": 1}},
    {"id": "R15", "filters": {},
     "text": "Build a working web prototype in JavaScript within a month, front end and back end.",
     "relevant": {"Jatin Wadhwa": 2, "Aryan Luthra": 1, "Zoya Khan": 1}},
    {"id": "R16", "filters": {},
     "text": "Recruit and onboard fifty new engineers over the next two quarters.",
     "relevant": {"Swati Bhandari": 2}},
]
