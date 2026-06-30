from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

content = """John Doe
Email: john@gmail.com
Phone: 9876543210

Location
Hyderabad, Telangana, India

Skills
Python
SQL
machine-learning

Education
B.Tech, Computer Science, ABC University, 2021

Experience
Software Engineer
ABC Pvt Ltd
Jan 2022 - Present

Links
LinkedIn: linkedin.com/in/johndoe
GitHub: github.com/johndoe
"""

for line in content.split('\n'):
    pdf.cell(200, 10, text=line, new_x="LMARGIN", new_y="NEXT", align='L')

pdf.output("data/input/resume.pdf")
print("Successfully generated data/input/resume.pdf")
