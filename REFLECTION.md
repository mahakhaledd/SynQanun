## 1) Challenges Faced

- **Steep Learning Curve:**  
  This was my first time working with this exact stack (FastAPI, regex-based parsing, and SQL Server integration). Getting the environment running and understanding how the pieces fit together was the biggest early challenge.

- **Data Heterogeneity:**  
  Designing a scalable schema for three different document types (Laws, Judgments, Fatwas) required careful structure analysis. Mapping these diverse formats into a clean relational model under a tight timeline was demanding.

- **Arabic Text Processing:**  
  Arabic legal documents vary in layout and wording. Building reliable regex patterns took multiple iterations to keep extraction accurate without breaking the state-machine parsing flow.

---

## 2) Potential Improvements

- **Dockerization :**  
  Package the API + database using Docker Compose for easier one-command deployment and consistent local setup.

---

 ## 3) Notes / Constraints

- **Time Constraints (on my side):**  
  The task timeline was reasonable, but my personal schedule was tight during the implementation period.  
  Because of that, I prioritized delivering a working end-to-end pipeline (parsing → loading → API) over optional enhancements like Dockerization and more advanced search.
