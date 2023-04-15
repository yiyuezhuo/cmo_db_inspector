
import gradio as gr

class ReferencesTab:
    def __init__(self):
        pass

    def build(self):
        gr.Markdown(r"""

Harpoon IV Signatures Definition:

| Contact Size | RCS Surf (db) | RCS Surf ($m^2$) | Sample Range $(nm)$ | RCS Air $(db)$ | RCS Air $m^2$ | Sample Range (nm) |
| ------------ | ------------- | ---------------- | ------------------- | -------------- | ------------- | ----------------- |
| Large        | 65            | 3,000,000        | 100                 | 18             | 63            | 100               |
| Medium       | 55            | 300,000          | 56                  | 10             | 10            | 63                |
| Small        | 45            | 30,000           | 32                  | 5              | 3.2           | 47                |
| Very Small   | 35            | 3,000            | 18                  | -10            | 0.1           | 20                |
| Stealthy     | 25            | 300              | 10                  | -30            | 0.001         | 6                  |

APG-65 (LD/SD) Harpoon data:

| Version    | Large | Medium | Small | Very Small | Stealthy |
|------------|-------|--------|-------|------------|----------|
| Harpoon IV | 160   | 101    | 75    |   32       | 10       |
| Harpoon V  | 160   | 112    | 80    |   32       | 10       |

Since Gradio's block equation support still doesn't work, checkout the experimental equation in the repo's readme:

https://github.com/yiyuezhuo/cmo_db_inspector

For data field explanation, see CMO's official `cmo-db-request` issue template, for example:

https://github.com/PygmalionOfCyprus/cmo-db-requests/blob/main/.github/ISSUE_TEMPLATE/21_NEW-SENSOR.yml

Due to current Gradio's limitation, double click on the same cell (i,j coordinates) in the table (even it's generated from another search), will not triiger click event. You can select its left or right cell to trigger the event.

""")
