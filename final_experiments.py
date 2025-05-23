from google import genai
from google.genai import types
from typing import List
import sys
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any   
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from token_tracker import record_token_usage, save_token_usage, display_token_usage_summary
import string

load_dotenv()

zeroshot_examples = ""
five_shot_examples = """
        Example 1:
    
    Content: "On behalf of Emory\u2019s Women in STEM organization, You are invited to their annual Networking Night!\n Join us on Wednesday, April 2nd, from 6-8 PMin the Math and Science Center (MSC) E208. This event will feature a panel of women professionals from STEM fields, who will share their experiences and discuss what it\u2019s like to work in these roles, as well as their journeys as women in STEM. The event will be informal and relaxed, with pizza and refreshments provided. It\u2019s a fantastic opportunity to meet professors, graduate students, and network with others in our community.\nIf you\u2019re interested in attending, please RSVP here: https://tr.ee/v9QfhkjLRQ\n       ____________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________\n  SUMMER RESEARCH PROGRAM: AI Xperience \nEmory\u2019s Center for AI Learning invites students toapply to AI.Xperience, its summer applied research program.In this program, students will have the opportunity to grow their data science and programming skills with hands-on learning. To be selected, students need to:\u00b7\n\t\u2022\tHave been enrolled in classes in the spring 2025 semester and be enrolled at Emory in the fall 2024 semester\n\t\u2022\tAttend 3 or 4 team meetings per week\n\t\u2022\tBe able to commit roughly 20 hours per week to the project over the 6-week period\n\t\u2022\tHave knowledge of common statistical analysis and machine learning methods\n\t\u2022\tHave experience programming in R and/or PythonAll interested students should applyby 11:59 PM on March 29, 2025.We look forward to reviewing your applications!\nAPPLY\n \n             Sadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: events, research
    
    Example 2:
    
    Content: "APPLICATION DEADLINE EXTENDED - MARCH 31ST IT IS NOT TOO LATE TO JOIN!!!\n LEARN MORE ABOUT THE QTM AMBASSADORS COHORT ON THE QTM WEBSITE\n https://quantitative.emory.edu/opportunities/ambassadors.html\n  APPLICATIONS ARE OPEN TO JOIN THE QTM DEPARTMENT AMBASSADORS TEAM FOR AY 2025 - 26. \n QTM Ambassadors are a selective cohort of sophomores, juniors, and seniors who are committed to service and leadership in the QTM community. As the department's student representatives, Ambassadors will engage with our external advisory board, assist with programming, andcultivate professional skills and relationships that will prove to be valuable long after graduation.\n Here are a few requirements and opportunities:\n \t\u2022\tMust be a QTM major or QTM minor\n\t\u2022\tMust have a strong sense of responsibility\n\t\u2022\tMust be available to meet on Fridays for 1 hour at least twice a month between the hours of 3:00 PM \u2013 4:30 PM\n\t\u2022\tNetwork with external partners\n\t\u2022\tSupport faculty and staff with QTM events\n\t\u2022\tBuild your professional portfolio \n\t\u2022\tFor more requirements and opportunities, see QTM website : https://quantitative.emory.edu/opportunities/ambassadors.html\n Application link is available below and on the QTM website. Applications are due March 31st \n  QTM Ambassador Application (2025 - 2026)\n We love for you to join us!\n  Sadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: careers
    
    
    Example 3:
    
    Content: "SPECIAL ANNOUNCEMENT\n   \n\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: Non
    
    Example 4:
    
    "content": "SPECIAL OPPORTUNITY\n\u00a0\n\u00a0\n\u00a0\n\nKey Highlights:\n\t\u2022\tDates: Saturday, October 12th - Wednesday, October 17th\u00a0(*students are usually provided a letter\u00a0 Associate Dean of\u00a0 the Pathways Center\u00a0excused from classes on Wednesday as this will be a travel day)\u00a0\n\t\u2022\tLocation: San Francisco, California\n\t\u2022\tFocus: STEM Careers\n\t\u2022\tApplication Open: August 29th, 2024 (LIVE NOW!)\n\t\u2022\tApplication Deadline: Sunday, September 8th, 2024, at 11:59 PM\u00a0\nEncourage your students to apply!\u00a0This program provides them with:\n\t\u2022\tExposure to diverse STEM fields:\u00a0Explore various career paths and gain real-world knowledge from industry professionals.\n\t\u2022\tNetworking opportunities:\u00a0Connect with successful Emory alumni working in STEM fields.\n\t\u2022\tProfessional development:\u00a0Build valuable networking and presentation skills.\n\t\u2022\tImmersive experience:\u00a0Explore San Francisco and engage in unique activities.\nLearn More:\n\t\u2022\tFull program details and application information: https://pathways.emory.edu/opportunities/career-trek/index.html\nPlease encourage students to apply, and share this information across your Canvas courses, listservs, etc. If students have any questions, please feel free to reach out\u00a0to the Pathways Center at cpd@emory.edu.\u00a0\u00a0\n\u00a0\n\u00a0\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: events
    
    
    Example 5:
    
    "content": "NEW CLASS ANNOUNCEMENTS\n\u00a0\nThere is a new section of QTM 302W section 3 open and there is only 15 seats.\u00a0 The course (class #6445) is on MW at 1:00 PM -2:15 PM taught by Dr. Ben Miller.\u00a0\u00a0 This course is permission code only and prefer graduating senior (who need this course to graduate).\u00a0\u00a0 This is a first come, first serve situation. \u00a0If there are seats left, we will take juniors.\u00a0 \u00a0\n\u00a0\nNew section \u00a0\nQTM 151- section 2 -\u00a0 \u00a0Introduction to Statistical Computing II - MW 4pm-4:50pm\u00a0in\u00a0Anthropology Building 303- have plenty of seats (103) \u2013 3 credit hour\nQTM 350- section 2\u00a0 - Data Science Computing - MW 2:30pm-3:45pm\u00a0in\u00a0Math & Science Center - E208\u00a0 - have plenty of seats (41) \u2013 3 credit hours\n\u00a0\nQTM 185 \u2013 Section 1 - Applied Topics in QTM: Data Science for Social Good \u2013 Fridays - 1pm-1:50pm\u00a0in ONLINE\u00a0 - 1 credit hour\nQTM 185 \u2013 section 2 - \u00a0Applied Topics in QTM: Generative AI/Real-World Appl\u00a0 - M 6pm-8pm\u00a0in\u00a0New Psyc Bldg 250 (36 Eagle Row) \u2013 2 credit hours \n\u00a0\nNew course\nQTM 185 \u2013 section 3 - Applied Topics in QTM: Ethical Emerging Technologies - Th 5pm-7pm\u00a0in\u00a0New Psyc Bldg 220 (36 Eagle Row) \u2013 2 credit hours\n\u00a0\nNew course\nQTM 285 \u2013 section 1 - Topics in Quantitative Science: Prediction, Inference & Causality - MW 4pm-5:15pm\u00a0in\u00a0New Psyc Bldg 230 (36 Eagle Row)\nLab Friday 2:30pm-3:20pm\u00a0in\u00a0New Psyc Bldg 220 (36 Eagle Row) This class will be accepted in place of QTM 220 as a prerequisite.\u00a0\u00a0 \u2013 4 credit hours\n\u00a0\nNew course\nQTM 285 \u00a0- section 2 - Topics in Quantitative Science: Unlocking the Future with AI \u2013 Wednesdays 4pm-7pm\u00a0in ONLINE \u2013 3 credit hours\n\u00a0\nBest, \n\u00a0\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: administration
    
    
    """
eight_shot_examples = """ 

    Examples:
    
    Example 1:
    
    Content: "On behalf of Emory\u2019s Women in STEM organization, You are invited to their annual Networking Night!\n Join us on Wednesday, April 2nd, from 6-8 PMin the Math and Science Center (MSC) E208. This event will feature a panel of women professionals from STEM fields, who will share their experiences and discuss what it\u2019s like to work in these roles, as well as their journeys as women in STEM. The event will be informal and relaxed, with pizza and refreshments provided. It\u2019s a fantastic opportunity to meet professors, graduate students, and network with others in our community.\nIf you\u2019re interested in attending, please RSVP here: https://tr.ee/v9QfhkjLRQ\n       ____________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________\n  SUMMER RESEARCH PROGRAM: AI Xperience \nEmory\u2019s Center for AI Learning invites students toapply to AI.Xperience, its summer applied research program.In this program, students will have the opportunity to grow their data science and programming skills with hands-on learning. To be selected, students need to:\u00b7\n\t\u2022\tHave been enrolled in classes in the spring 2025 semester and be enrolled at Emory in the fall 2024 semester\n\t\u2022\tAttend 3 or 4 team meetings per week\n\t\u2022\tBe able to commit roughly 20 hours per week to the project over the 6-week period\n\t\u2022\tHave knowledge of common statistical analysis and machine learning methods\n\t\u2022\tHave experience programming in R and/or PythonAll interested students should applyby 11:59 PM on March 29, 2025.We look forward to reviewing your applications!\nAPPLY\n \n             Sadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: events, research
    
    Example 2:
    
    Content: "APPLICATION DEADLINE EXTENDED - MARCH 31ST IT IS NOT TOO LATE TO JOIN!!!\n LEARN MORE ABOUT THE QTM AMBASSADORS COHORT ON THE QTM WEBSITE\n https://quantitative.emory.edu/opportunities/ambassadors.html\n  APPLICATIONS ARE OPEN TO JOIN THE QTM DEPARTMENT AMBASSADORS TEAM FOR AY 2025 - 26. \n QTM Ambassadors are a selective cohort of sophomores, juniors, and seniors who are committed to service and leadership in the QTM community. As the department's student representatives, Ambassadors will engage with our external advisory board, assist with programming, andcultivate professional skills and relationships that will prove to be valuable long after graduation.\n Here are a few requirements and opportunities:\n \t\u2022\tMust be a QTM major or QTM minor\n\t\u2022\tMust have a strong sense of responsibility\n\t\u2022\tMust be available to meet on Fridays for 1 hour at least twice a month between the hours of 3:00 PM \u2013 4:30 PM\n\t\u2022\tNetwork with external partners\n\t\u2022\tSupport faculty and staff with QTM events\n\t\u2022\tBuild your professional portfolio \n\t\u2022\tFor more requirements and opportunities, see QTM website : https://quantitative.emory.edu/opportunities/ambassadors.html\n Application link is available below and on the QTM website. Applications are due March 31st \n  QTM Ambassador Application (2025 - 2026)\n We love for you to join us!\n  Sadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: careers
    
    
    Example 3:
    
    Content: "SPECIAL ANNOUNCEMENT\n   \n\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: Non
    
    Example 4:
    
    "content": "SPECIAL OPPORTUNITY\n\u00a0\n\u00a0\n\u00a0\n\nKey Highlights:\n\t\u2022\tDates: Saturday, October 12th - Wednesday, October 17th\u00a0(*students are usually provided a letter\u00a0 Associate Dean of\u00a0 the Pathways Center\u00a0excused from classes on Wednesday as this will be a travel day)\u00a0\n\t\u2022\tLocation: San Francisco, California\n\t\u2022\tFocus: STEM Careers\n\t\u2022\tApplication Open: August 29th, 2024 (LIVE NOW!)\n\t\u2022\tApplication Deadline: Sunday, September 8th, 2024, at 11:59 PM\u00a0\nEncourage your students to apply!\u00a0This program provides them with:\n\t\u2022\tExposure to diverse STEM fields:\u00a0Explore various career paths and gain real-world knowledge from industry professionals.\n\t\u2022\tNetworking opportunities:\u00a0Connect with successful Emory alumni working in STEM fields.\n\t\u2022\tProfessional development:\u00a0Build valuable networking and presentation skills.\n\t\u2022\tImmersive experience:\u00a0Explore San Francisco and engage in unique activities.\nLearn More:\n\t\u2022\tFull program details and application information: https://pathways.emory.edu/opportunities/career-trek/index.html\nPlease encourage students to apply, and share this information across your Canvas courses, listservs, etc. If students have any questions, please feel free to reach out\u00a0to the Pathways Center at cpd@emory.edu.\u00a0\u00a0\n\u00a0\n\u00a0\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: events
    
    
    Example 5:
    
    "content": "NEW CLASS ANNOUNCEMENTS\n\u00a0\nThere is a new section of QTM 302W section 3 open and there is only 15 seats.\u00a0 The course (class #6445) is on MW at 1:00 PM -2:15 PM taught by Dr. Ben Miller.\u00a0\u00a0 This course is permission code only and prefer graduating senior (who need this course to graduate).\u00a0\u00a0 This is a first come, first serve situation. \u00a0If there are seats left, we will take juniors.\u00a0 \u00a0\n\u00a0\nNew section \u00a0\nQTM 151- section 2 -\u00a0 \u00a0Introduction to Statistical Computing II - MW 4pm-4:50pm\u00a0in\u00a0Anthropology Building 303- have plenty of seats (103) \u2013 3 credit hour\nQTM 350- section 2\u00a0 - Data Science Computing - MW 2:30pm-3:45pm\u00a0in\u00a0Math & Science Center - E208\u00a0 - have plenty of seats (41) \u2013 3 credit hours\n\u00a0\nQTM 185 \u2013 Section 1 - Applied Topics in QTM: Data Science for Social Good \u2013 Fridays - 1pm-1:50pm\u00a0in ONLINE\u00a0 - 1 credit hour\nQTM 185 \u2013 section 2 - \u00a0Applied Topics in QTM: Generative AI/Real-World Appl\u00a0 - M 6pm-8pm\u00a0in\u00a0New Psyc Bldg 250 (36 Eagle Row) \u2013 2 credit hours \n\u00a0\nNew course\nQTM 185 \u2013 section 3 - Applied Topics in QTM: Ethical Emerging Technologies - Th 5pm-7pm\u00a0in\u00a0New Psyc Bldg 220 (36 Eagle Row) \u2013 2 credit hours\n\u00a0\nNew course\nQTM 285 \u2013 section 1 - Topics in Quantitative Science: Prediction, Inference & Causality - MW 4pm-5:15pm\u00a0in\u00a0New Psyc Bldg 230 (36 Eagle Row)\nLab Friday 2:30pm-3:20pm\u00a0in\u00a0New Psyc Bldg 220 (36 Eagle Row) This class will be accepted in place of QTM 220 as a prerequisite.\u00a0\u00a0 \u2013 4 credit hours\n\u00a0\nNew course\nQTM 285 \u00a0- section 2 - Topics in Quantitative Science: Unlocking the Future with AI \u2013 Wednesdays 4pm-7pm\u00a0in ONLINE \u2013 3 credit hours\n\u00a0\nBest, \n\u00a0\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: administration
    
    
    Example 6:
    
    "content": "SPECIAL ANNOUNCEMENT\n\u00a0\n\u00a0\nAnnouncement from summer programs: \n\u00a0\nNow is a good time to plan the remainder of your academic year. We are offering a\u00a0Maymester course\u00a0this summer. It is a three-week intensive course that may fulfill a GER or graduation requirement.\u00a0\n\u00a0\nSummer School\u00a0will be having an\u00a0Info Stop\u00a0to provide more information about Maymester course offerings. Be sure to stop by their table to learn more along with summer and semester options through\u00a0Education Abroad.\n\u00a0\nDates & deadlines\nWed, Jan 31: Maymester & Study Abroad Info Stop -- 11:00a-1:30p, ESC South Commons\nTue, Feb 13: Summer enrollment opens\nThur, Feb 15: Application deadline for most summer abroad programs\n\u00a0\nFor questions, please send an email to\u00a0Summer Programs\u00a0or\u00a0Education Abroad.\n\u00a0\nBest, \n\u00a0\n\u00a0\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: administration
    
    Example 7:
    
    "content": "SPECIAL ANNOUNCEMENT\n\u00a0\nDr. Kevin McAlister(QTM Director of Research) and Dr. Jin Kim (QTM Director of Undergraduate Studies) will be conducting an advising session for all QTM Majors and Minors on Friday, January 19th at 12:30 PM \u2013 2:00PM at the Psychology Building in PAIS 290 Auditorium. This is a very important meeting for all QTM Students(QSS, AMS, PPA, & QSS Minors)regarding course requirements for your major or minor. Seniors, this is especially important for you to ensure you are taking the correct courses to complete your degree as add/drop/swap ends on January 30th.\n\u00a0\nThose of you who have questions regarding the capstone program, honors program, Internships, overlap courses, course substitutes, etc., please attend as well. \n\u00a0\nIf you have questions regarding this meeting, please contact me. Thanks. \n\u00a0\nBest, \u00a0\n\u00a0\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: events
    
    Example 8:
    
    "content": "For QTM Undergraduates\n\nWednesday, \nNovember 22,\u00a0 2023Add/Drop/Swap starts \u2013 Monday, November 20th nOPPORTUNITY\u00a0\nSpring 2024 QTM Undergraduate Teaching & Mentorship Application\n\u00a0\nThe Spring 2024 QTM Undergraduate Teaching & Mentorship Application is now open. We are seeking TAs, Lab Assistants, and Graders for QTM 100, 110, 150, 151, 200, 210, 220, and 350. Please complete the application at https://forms.office.com/r/vR2YxeY4gp. You must be signed in with your Emory student credentials to access the application form. If you have questions about spring positions or the application form, please contact Lora McDonald (lora.mcdonald@emory.edu). \n\u00a0\nSee attached for more details \n\u00a0\nSubmitted by Lora McDonald\\nOpportunityTHE MARCUS AUTISM CENTER\nThe Marcus Autism Center, in conjunction with the Emory University School of Medicine and Children's Healthcare of Atlanta, is offering five fellowships: the Cohen Fellowship in Developmental Social Neuroscience, the Simons Fellowship in Computational Neuroscience, the Louise and Brett Samsky Fellowship in Educational Science and Practice, the Sally Provence Fellowship in Clinical Research, and the ACCESS Fellowship in Implementation Science. \nStudents who will receive a bachelor's degree by June 2024 will be eligible for the positions. The fellowships will commence in July 2024, and they are 2 years in duration. Students can find further details here. \nAttached, please find a brochure describing the fellowships. Please feel free to print the brochure and post it in your department. I ask that you let us know that you have received this e-mail and that you forward it, along with the associated brochure, to students in the Department of Quantitative Theory and Methods. \nThe Cohen Fellowship in Developmental Social Neuroscience will involve cutting-edge social neuroscience and/or neuroimaging research in infants, toddlers and adolescents. Fellows will work to further the understanding of autism through eye-tracking research, guiding a project from the point of data collection to publication of results. \nThe Simons Fellowship in Computational Neuroscience will involve integrating computational strategies with clinical research goals. Fellows will develop methods for the analysis of visual scanning and eye-tracking data, computational models of visual salience, and data visualization techniques, all with the aim of advancing the understanding of autism and efforts at early diagnosis. \nThe Louise and Brett Samsky Fellowship in Educational Science and Practice will involve research in educational innovations in autism. Fellows will learn about classroom-based interventions to increase social emotional engagement and inclusion, gaining experiences with observational research methods, practical experience through direct classroom responsibilities, cutting edge intervention research, and implementation science approaches. \nThe Sally Provence Fellowship in Clinical Research will select fellows for a two-year training in clinical assessment measures and research methodologies to better understand ASD and related disabilities. \nThe ACCESS Fellowship in Implementation Science will select fellows for a two-year training in research focused on community engagement participatory methods, translating evidence-based treatments for autism into community settings, as well as the processes and partnerships that support these efforts. \nThank you for your help! We look forward to hearing from you. \nSincerely, Marcus Predoctoral Fellowship Committee See attached flyer\n\nPrerequisites\nYou must complete ALL prerequisites listed in order to enroll in these courses.\nQTM 210\n\t\u2022\tEither QTM 120 or MATH 210 or MATH 211\nQTM 220\n\t\u2022\tQTM 110\n\t\u2022\tQTM 150\n\t\u2022\tQTM 210 or ECON 220 or MATH 361 with a plan to co-enroll in MATH 362\n\t\u2022\tMATH 210 or MATH 211\n\t\u2022\tMATH 221\nElective Prerequisites\n\t\u2022\tQTM 385 prerequisites will be listed in the course description!!!\n\u00a0\nEquivalents\nBelow are courses that act as equivalents to the respective QTM courses\nQTM 210:\n\t\u2022\tECON 220 and [MATH 210 or MATH 211]\n\t\u2022\tOR - MATH 362\nQTM 220:\n\t\u2022\tECON 320 plus QTM 110, QTM 150, MATH 221 and [MATH 210 or MATH 211]\n\u00a0\nFor General Academic Advising\nSchedule an appointment at\u00a0https://calendly.com/emoryqtm.\n\u00a0\nIf you have any questions regarding the above information, please do not hesitate to reach out.\n\u00a0\nBest,\nSadie Hannans\nQTM Program Coordinator\nShanna9@emory.edu\u00a0\u00a0 470-620-7981\n\n\n\u00a0\n\n\u00a0\n\u00a0\n\n\u00a0\u00a0\u00a0\n\u00a0\n\u00a0\u00a0\u00a0\u00a0\u00a0\n\n\u00a0\u00a0\u00a0\n\n\n\n\nPROFESSIONAL DEVELOPMENT\n\nQTM Preparation: A Pathway to Professionalism\n\u00a0\nNew Resources Available\n\n\u00a0\n\u00a0Getting Started with SQL\n\n\u00a0\nGit and GitHub\n\u00a0\n\n\u00a0\n\u00a0\n\u00a0\n\u00a0\n\nQTM DataCamp Access\nQTM Access to DataCamp is now back in business! Sign up here.\nConnect with Emory Alumni\n\nEmory Connects is a platform sponsored by Emory Alumni and Engagement and is a space for current students and alumni to connect and network. Log in to\u00a0Emory Connects\u00a0today to see what is available!\n\u00a0\n\nQTM DataCamp Access\n\nQTM Access to DataCamp is now back in business! Sign up here.\n\u00a0\n\u00a0\n\n\u00a0\nLooking for a spring or summer internship or full-time job?\n\nCheck out the attached document for tips on internship/job searches. Positions are still being posted on Handshake and many are still accepting applications.\u00a0Log on to Handshake\u00a0to check out some of the roles!\n\n\u00a0\u00a0\n\u00a0\n\u00a0\nSadie Hannans\nUndergraduate Program Coordinator\nDepartment of Quantitative Theory & Methods\nEmory University\nEmail: shanna9@emory.edu | 470-620-7981\n(she/her/hers)"
    
    correct keywords: careers


        """

def setup_client():
    """
    setting up the client for google genai
    """
    # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_API_KEY = 'AIzaSyARSNi3GkruKJ7c9IEPQkasJQ_jHFHLDhM'
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY is not set. Please set it in your environment.")
        sys.exit(1)
    client = genai.Client(api_key=GOOGLE_API_KEY)
    return client

client = setup_client()

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")
    
def preprocess_email(email_text: str) -> str:
    """
    Preprocess email text by tokenizing, lemmatizing, and removing stopwords.
    
    Args:
        email_text: The raw email text
        
    Returns:
        Preprocessed email text
    """
    # Convert emails to lower case
    email_text = email_text.lower()
    
    # Tokenize the email text
    doc = nlp(email_text)
    
    # Lemmatize, remove stopwords, and punctuation
    lemmatized_tokens = [token.lemma_ for token in doc if token.text not in STOP_WORDS and token.text not in string.punctuation]
    
    # Join the lemmatized tokens back into a string
    processed_text = " ".join(lemmatized_tokens)
    
    return processed_text

def keyword_preprocessing(keywords: str) -> List[str]:
    """
    Preprocess the user-defined keywords into a list.
    
    Args:
        keywords: Comma-separated string of keywords
        
    Returns:
        List of cleaned keywords
    """
    return [keyword.strip() for keyword in keywords.lower().split(",")]

def call_llm(client, content: str, instruction: str, model: str = "gemini-2.0-flash") -> str:
    """
    Call the language model to generate a response based on the content and instruction.
    
    Args:
        client: The generative AI client
        content: The email content to be classified
        instruction: The system instruction for the model
        model: The model to use for generation
        
    Returns:
        The model's response text
    """
    try:
        print(f"Calling LLM with {len(content)} characters of content")
        response = client.models.generate_content(
        model=model,
        contents=[content], # here should the content of email be
        config=types.GenerateContentConfig(
            max_output_tokens=1024,
            temperature=0.1,
            system_instruction= instruction,
        )
        )
        record_token_usage(content, instruction, model, response)
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            print("Unexpected response format:", response)
            return str(response)
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return f"Error: {str(e)}"

def classify_email(email_content: str, keywords: List[str], client, number_of_keywords: int, fewshot_examples: str = "", controlled: bool = False) -> Dict[str, Any]:

    KEYWORDS = keywords

    
    PROMPT_CLASSIFICATION = f"""
    You are an email classification assistant. Your task is to analyze the content of emails and identify which of the following keywords are relevant to the email:

    [{KEYWORDS}] 

    
    Instructions:
    1. Analyze the full email content provided
    2. Identify any keywords from the list that are relevant to the email, and only return one keyword that is most closely related to the email
    3. Return ONLY one relevant keyword
    4. If no keywords match, return "Non"
    5. The keywords should be assigned only if the cotent of email is closely related to the keywords!
    
    
    Return your classification in this format:
    KEYWORDS: <relevant keywords (separated by commas) or Non>
    
    
    Do not include any additional explanation or analysis in your response.
    """
    
    PROMPT_CLASSIFICATION_CONTROLLED = f"""
    You are an email classification assistant. Your task is to analyze the content of emails and identify which of the following keywords are relevant to the email:

    [{KEYWORDS}] 

    
    Instructions:
    1. Analyze the full email content provided
    2. Identify any keywords from the list that are relevant to the email, and only return one keyword that is most closely related to the email
    3. Return ONLY one relevant keyword
    4. If no keywords match, return "Non"
    5. The keywords should be assigned only if the cotent of email is closely related to the keywords!
    
    
    Return your classification in this format:
    You should return exactly {number_of_keywords} keywords
    KEYWORDS: <relevant keywords (separated by commas) or Non>
    
    
    Do not include any additional explanation or analysis in your response.
    """
    
    # Add examples if provided
    if fewshot_examples:
        PROMPT_CLASSIFICATION += f"\n\nHere are some examples:\n{fewshot_examples}"
        PROMPT_CLASSIFICATION_CONTROLLED += f"\n\nHere are some examples:\n{fewshot_examples}"
    
    if controlled:
        response = call_llm(client, content=email_content, instruction=PROMPT_CLASSIFICATION_CONTROLLED)
    else:
        response = call_llm(client, content=email_content, instruction=PROMPT_CLASSIFICATION)
    
    # Parse the result
    try:
        keywords_line = next((line for line in response.strip().split('\n') if line.startswith('KEYWORDS:')), '')
        found_keywords = keywords_line.replace('KEYWORDS:', '').strip()
        
        if found_keywords.upper() == 'NONE' or found_keywords.upper() == 'NON':
            return {
                'relevant_keywords': [],
                'raw_result': response
            }
        else:
            return {
                'relevant_keywords': [kw.strip().lower() for kw in found_keywords.split(',')],
                'raw_result': response
            }
    except Exception as e:
        print(f"Error parsing classification result: {str(e)}")
        return {
            'relevant_keywords': [],
            'raw_result': response,
            'error': str(e)
        }

with open('/Users/natehu/Desktop/QTM 329 Comp Ling/EmaiLLM/data/qtm_emails_final_version.json', 'r') as f:
    all_qtm_emails = json.load(f)
    
import tqdm


def run_experiments():
    """
    Run all experiment configurations and save results with descriptive filenames.
    Conditions:
    1. Without specifying keyword count
    2. With specified keyword count (from manual labeling)
    
    For each condition, run:
    - 0-shot learning
    - 5-shot learning
    - 8-shot learning
    """
    try:
        # Define experiment configurations
        conditions = [
            {"name": "uncontrolled", "controlled": False, "description": "without_keyword_count_control"},
            {"name": "controlled", "controlled": True, "description": "with_keyword_count_control"}
        ]
        
        shots = [
            {"name": "0shot", "examples": ""},
            {"name": "5shot", "examples": five_shot_examples},
            {"name": "8shot", "examples": eight_shot_examples}
        ]
        
        # Get unique keywords from all emails
        keywords = []
        for email in all_qtm_emails:
            keywords.extend(email['category'])
        unique_keywords = list(set(keywords))
        if 'Non' in unique_keywords:
            unique_keywords.remove('Non')
        finalkeywords = ", ".join(unique_keywords)
        
        print(f"Running experiments with the following keywords: {finalkeywords}")
        
        # Ensure output directory exists
        output_dir = '/Users/natehu/Desktop/QTM 329 Comp Ling/EmaiLLM/final_experiments'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
        # Run each experiment configuration
        for condition in conditions:
            for shot in shots:
                try:
                    print(f"\n===============================================")
                    print(f"Running experiment: {condition['name']}_{shot['name']}")
                    print(f"===============================================")
                    output = []
                    
                    for i, email in enumerate(tqdm.tqdm(all_qtm_emails)):
                        try:
                            content = email['subject'] + ' ' + email['content']
                            len_keywords = len(set(email['category']))
                            classification = classify_email(
                                email_content=content,
                                keywords=finalkeywords,
                                client=client,
                                number_of_keywords=len_keywords,
                                fewshot_examples=shot["examples"],
                                controlled=condition["controlled"]
                            )
                            output.append({
                                'email_id': email.get('id', i),
                                'predicted_classification': classification,
                                'actual_classification': email['category'],
                                'email_content': content[:100] + "..." # Store truncated content for reference
                            })
                        except Exception as e:
                            print(f"Error processing email {i}: {str(e)}")
                            # Add error info to output
                            output.append({
                                'email_id': email.get('id', i),
                                'error': str(e),
                                'actual_classification': email.get('category', []),
                                'email_content': email.get('content', '')[:100] + "..." if 'content' in email else "No content"
                            })
                    
                    # Save results with descriptive filename
                    filename = f"{condition['description']}_{shot['name']}.json"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'w') as f:
                        json.dump(output, f, indent=4)
                    
                    print(f"Saved results to {filepath}")
                    
                    # Save token usage after each experiment
                    token_usage_file = os.path.join(output_dir, f"{condition['description']}_{shot['name']}_token_usage.json")
                    save_token_usage(token_usage_file)
                    print(f"Saved token usage to {token_usage_file}")
                
                except Exception as exp:
                    print(f"Error running experiment {condition['name']}_{shot['name']}: {str(exp)}")
        
        print("\nAll experiments completed successfully!")
    
    except Exception as e:
        print(f"Fatal error in run_experiments: {str(e)}")
        raise

# Run all experiments
if __name__ == "__main__":
    print("Starting email classification experiments...")
    try:
        run_experiments()
        display_token_usage_summary()
        print("Experiment completed successfully!")
    except KeyboardInterrupt:
        print("\nExperiment was interrupted by user.")
    except Exception as e:
        print(f"\nExperiment failed with error: {str(e)}")
        import traceback
        traceback.print_exc()