import base64
import datetime
import io
import random
import time

import docx2txt

import pandas as pd
import plotly.express as px
import pymysql
import streamlit as st
from PIL import Image
from pdfminer3.converter import TextConverter
from pdfminer3.layout import LAParams
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfpage import PDFPage
from pyresparser import ResumeParser
from streamlit_tags import st_tags
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity



from Courses import ds_course, web_course, android_course, ios_course, uiux_course




def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resouces_mnger = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resouces_mnger, fake_file_handle, laparams=LAParams())
    pge_interpreter = PDFPageInterpreter(resouces_mnger, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            pge_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_viewer = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_viewer, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c1 = 0
    recomended_courses = []
    numb_record = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for course_name, course_link in course_list:
        c1 += 1
        st.markdown(f"({c1}) [{course_name}]({course_link})")
        recomended_courses.append(course_name)
        if c1 == numb_record:
            break
    return recomended_courses


connection = pymysql.connect(host='localhost', user='root', password='', db='sra')
cursor = connection.cursor()


def insert_data(name, email, res_score, timestamp, no_of_pages, recomended_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insrt_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
        name, email, str(res_score), timestamp, str(no_of_pages), recomended_field, cand_level, skills, recommended_skills,
        courses)
    cursor.execute(insrt_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="Smart Resume Analyzer",
    page_icon='final.png',
)


def run():
    st.title("Smart Resume Selector & Analyzer")
    st.sidebar.markdown("# Choose User")
    activtity = ["Normal User", "Admin", "Check Match"]
    choices = st.sidebar.selectbox("Choose among the given options:", activtity)

    image = Image.open('resume_selector.jpg')

    image = image.resize((300, 270))
    st.image(image)

    # Create the DB
    database_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(database_sql)

    # Create table
    DB_table_name = 'user_data'
    tbl_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     score_res VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(tbl_sql)
    if choices == 'Normal User':

        resume_file = st.file_uploader("Choose your Resume in PDF Format", type=["pdf"])
        if resume_file is not None:

            image_path = './Uploaded_Resumes/' + resume_file.name
            with open(image_path, "wb") as f:
                f.write(resume_file.getbuffer())
            show_pdf(image_path)
            data_resume = ResumeParser(image_path).get_extracted_data()
            if data_resume:
                # Get the whole resume data
                resume_txt = pdf_reader(image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + data_resume['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + data_resume['name'])
                    st.text('Email: ' + data_resume['email'])
                    st.text('Contact: ' + data_resume['mobile_number'])
                    st.text('Resume pages: ' + str(data_resume['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if data_resume['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                                unsafe_allow_html=True)
                elif data_resume['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif data_resume['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)

                st.subheader("**Skills Recommendation💡**")
                # Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=data_resume['skills'], key='1')

                #  recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

                recommended_skills = []
                recomended_field = ''
                recomended_courses = ''
                # Courses recommendation
                for i in data_resume['skills']:
                    # Data science recommendation
                    if i.lower() in ds_keyword:

                        recomended_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        recomended_courses = course_recommender(ds_course)
                        break

                    # Web development recommendation
                    elif i.lower() in web_keyword:

                        recomended_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        recomended_courses = course_recommender(web_course)
                        break

                    # Android App Development
                    elif i.lower() in android_keyword:

                        recomended_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Job **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        recomended_courses = course_recommender(android_course)
                        break

                    # IOS App Development
                    elif i.lower() in ios_keyword:

                        recomended_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Job **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        recomended_courses = course_recommender(ios_course)
                        break

                    # Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:

                        recomended_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        recomended_courses = course_recommender(uiux_course)
                        break

                # Insert into table
                ts = time.time()
                current_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                current_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(current_date + '_' + current_time)

                # Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                score_res = 0
                if ('Objective' or 'OBJECTIVE') in resume_txt:
                    score_res = score_res + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if ('Declaration' or 'DECLARATION') in resume_txt:
                    score_res = score_res + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration✍/h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' or 'Interests' in resume_txt:
                    score_res = score_res + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_txt:
                    score_res = score_res + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if (('Projects') or ('PROJECTS')) in resume_txt:
                    score_res = score_res + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(score_res):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **")
                st.balloons()

                insert_data(data_resume['name'], data_resume['email'], str(score_res), timestamp,
                            str(data_resume['no_of_pages']), recomended_field, cand_level, str(data_resume['skills']),
                            str(recommended_skills), str(recomended_courses))


                connection.commit()
            else:
                st.error('Something went wrong..')
    elif choices == 'Admin':
        ## Admin Side
        st.success('Welcome to Admin Side')


        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'aastha' and ad_password == 'aastha123':
                st.success("Welcome Aastha")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                ## Pie chart for predicted field recommendations
                labels = plot_data.Predicted_Field.unique()
                print(labels)
                values = plot_data.Predicted_Field.value_counts()
                print(values)
                st.subheader("📈 **Pie-Chart for Predicted Field Recommendations**")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills')
                st.plotly_chart(fig)

                ### Pie chart for User's👨‍💻 Experienced Level
                labels = plot_data.User_level.unique()
                values = plot_data.User_level.value_counts()
                st.subheader("📈 ** Pie-Chart for User's👨‍💻 Experienced Level**")
                fig = px.pie(df, values=values, names=labels, title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                st.plotly_chart(fig)


            else:
                st.error("Wrong ID & Password Provided")

    else :
        pdf_file_resume = st.file_uploader("Choose your Resume in DOCX format", type=["docx"])
        pdf_file_jd = st.file_uploader("Upload job Description in DOCX format", type=["docx"])
        if pdf_file_resume is not None:
            if pdf_file_jd is not None:
               resume = docx2txt.process(pdf_file_resume)
               job_description = docx2txt.process(pdf_file_jd)
               text = [resume, job_description]


               cv = CountVectorizer()
               count_matrix = cv.fit_transform(text)

               per_matches = cosine_similarity(count_matrix)[0][1] * 100
               per_matches = round(per_matches, 2)
               st.markdown(
                   """
                   <style>
                       .stProgress > div > div > div > div {
                           background-color: #d73b5c;
                       }
                   </style>""",
                   unsafe_allow_html=True,
               )
               my_bar = st.progress(0)
               score = 0

               for percent_complete in range(int(per_matches)):
                   score += 1
                   time.sleep(0.1)
                   my_bar.progress(percent_complete + 1)
               st.success('** Your resume matches about: ' + str(per_matches) + '% of the job description **')
               st.warning(
                   "** Note: This score is calculated based on the content that you have added in your Resume. **")
               st.balloons()




run()
