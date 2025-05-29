from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def create_dummy_cv_pdf(filename="dummy_cv.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(name='Justify', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='H1Center', parent=styles['h1'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionTitle', parent=styles['h2'], spaceBefore=0.2*inch, spaceAfter=0.1*inch))
    styles.add(ParagraphStyle(name='SubHeading', parent=styles['h3'], spaceBefore=0.1*inch, textColor='grey')) # For job titles, degrees
    styles.add(ParagraphStyle(name='BoldSubText', parent=styles['Normal'], fontName='Helvetica-Bold'))


    Story = []

    # --- Content ---
    # Name
    Story.append(Paragraph("John Doe", styles['H1Center']))
    Story.append(Spacer(1, 0.1*inch))

    # Contact Information
    Story.append(Paragraph("<u>Contact Information</u>", styles['SectionTitle']))
    Story.append(Paragraph("Email: john.doe@example.com | Phone: (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe", styles['Normal']))
    Story.append(Paragraph("GitHub: github.com/johndoe | Portfolio: johndoe.dev", styles['Normal']))
    Story.append(Spacer(1, 0.2*inch))

    # Summary
    Story.append(Paragraph("<u>Summary</u>", styles['SectionTitle']))
    Story.append(Paragraph(
        "A highly motivated and skilled software engineer with experience in Python, Java, and web development. "
        "Proven ability to lead projects and contribute to team success.", styles['Normal']
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Skills
    Story.append(Paragraph("<u>Skills</u>", styles['SectionTitle']))
    Story.append(Paragraph("<b>Programming Languages:</b> Python, Java, C++, JavaScript, SQL", styles['Normal']))
    Story.append(Paragraph("<b>Frameworks & Technologies:</b> Spring Boot, Django, React, Node.js", styles['Normal']))
    Story.append(Paragraph("<b>Tools:</b> Git, Docker, Kubernetes, Jenkins, AWS", styles['Normal']))
    Story.append(Paragraph("<b>Databases:</b> PostgreSQL, MongoDB, Redis", styles['Normal']))
    Story.append(Spacer(1, 0.2*inch))

    # Work Experience
    Story.append(Paragraph("<u>Work Experience</u>", styles['SectionTitle']))
    # Job 1
    Story.append(Paragraph("Senior Software Engineer", styles['SubHeading']))
    Story.append(Paragraph("<b>Tech Solutions Inc.</b> | Jan 2021 - Present", styles['BoldSubText']))
    Story.append(Paragraph("- Developed new features for the company's flagship product using Python and Django.", styles['Normal']))
    Story.append(Paragraph("- Led a scrum team of 5 engineers, overseeing project planning and execution.", styles['Normal']))
    Story.append(Paragraph("- Mentored junior developers and conducted code reviews.", styles['Normal']))
    Story.append(Spacer(1, 0.1*inch))
    
    # Job 2
    Story.append(Paragraph("Software Engineer", styles['SubHeading']))
    Story.append(Paragraph("<b>Innovate Corp.</b> | Jun 2019 - Dec 2020", styles['BoldSubText']))
    Story.append(Paragraph("- Contributed to the development of a microservices-based application using Java and Spring Boot.", styles['Normal']))
    Story.append(Paragraph("- Assisted with testing, bug fixing, and improving application performance.", styles['Normal']))
    Story.append(Spacer(1, 0.2*inch))

    # Education
    Story.append(Paragraph("<u>Education</u>", styles['SectionTitle']))
    # Degree 1
    Story.append(Paragraph("Master of Science in Computer Science", styles['SubHeading']))
    Story.append(Paragraph("<b>XYZ University</b> | Graduated: May 2020", styles['BoldSubText']))
    Story.append(Paragraph("Relevant Coursework: Data Structures, Advanced Algorithms, Machine Learning.", styles['Normal']))
    Story.append(Paragraph("Thesis: Applied Machine Learning to XYZ problem.", styles['Normal']))
    Story.append(Spacer(1, 0.1*inch))

    # Degree 2
    Story.append(Paragraph("Bachelor of Science in Software Engineering", styles['SubHeading']))
    Story.append(Paragraph("<b>ABC College</b> | Graduated: Dec 2018", styles['BoldSubText']))
    Story.append(Paragraph("Minor: Mathematics", styles['Normal']))
    Story.append(Paragraph("Capstone Project: Developed a mobile application for campus navigation.", styles['Normal']))
    Story.append(Spacer(1, 0.2*inch))

    # Projects
    Story.append(Paragraph("<u>Projects</u>", styles['SectionTitle']))
    # Project 1
    Story.append(Paragraph("Personal Portfolio Website", styles['SubHeading']))
    Story.append(Paragraph("<b>Tech Stack:</b> HTML, CSS, JavaScript, Flask (Python)", styles['Normal']))
    Story.append(Paragraph("- Developed and deployed a responsive personal portfolio website to showcase projects and skills.", styles['Normal']))
    Story.append(Paragraph("Link: github.com/johndoe/portfolio", styles['Normal']))
    Story.append(Spacer(1, 0.1*inch))

    # Project 2
    Story.append(Paragraph("AI Powered Recommendation System", styles['SubHeading']))
    Story.append(Paragraph("<b>Tech Stack:</b> Python, Pandas, Scikit-learn", styles['Normal']))
    Story.append(Paragraph("- Built a content-based recommendation system for movies using collaborative filtering techniques.", styles['Normal']))
    
    doc.build(Story)
    print(f"'{filename}' created successfully.")

if __name__ == "__main__":
    create_dummy_cv_pdf()
