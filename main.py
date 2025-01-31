import streamlit as st
import os
from crewai import Agent, Task, Crew
from crewai_tools import TXTSearchTool, PDFSearchTool
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
os.environ["LD_LIBRARY_PATH"] = os.path.expanduser("~/sqlite/lib")
os.environ["PATH"] = os.path.expanduser("~/sqlite/bin") + ":" + os.environ["PATH"]

import sqlite3
print("SQLite version:", sqlite3.sqlite_version)  # Should print 3.35.0+

import chromadb  # Now Chroma should work fine


class MessageHistory:
    def __init__(self):
        self.l1 = []

    def add(self, user_message, ai_response):
        self.l1.append({'role': 'user', 'content': user_message})
        self.l1.append({'role': 'assistant', 'content': ai_response})

    def show_history(self):
        return self.l1

    def clear(self):
        self.l1 = []

def create_interviewer_agent(jd_tool, resume_tool):
    return Agent(
        role="Expert Interviewer",
        goal="Conduct a structured interview by asking relevant questions based on the job description and the candidate's resume.",
        backstory="You are an experienced interviewer skilled in assessing candidates based on job requirements and their qualifications.",
        tools=[jd_tool, resume_tool],
        memory=True,
        verbose=True
    )

def create_analysis_agent(jd_tool, resume_tool):
    return Agent(
        role="Talent Acquisition Expert",
        goal="Evaluate the candidate's fit for the job based on the job description, resume, and interview script analysis.",
        backstory="You are an expert in talent acquisition, specializing in evaluating candidates based on their resumes, job descriptions, and interview performance.",
        tools=[jd_tool, resume_tool],
        memory=True,
        verbose=True
    )

def initialize_llm():
    return ChatGroq(
        api_key=st.secrets["GROQ_API_KEY"],
        model="gemma2-9b-it",
        temperature=0
    )

def create_chat_chain(llm, question_set, history):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an Interviewer"),
        ("system", "You have a set of questions: {question_set}. Ask them sequentially, one at a time."),
        ("system", "Only ask the next unanswered question from {question_set}."),
        ("system", "Do not repeat any question already present in chat history."),
        ("system", "Ask only the question itself, without any additional text."),
        ("system", "Never answer the questions yourself"),
        ("system", "After questions are over say Thank You"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{answer}")
    ])
    return prompt | llm

def main():
    st.title("AI Interviewer System")
    
    if 'history' not in st.session_state:
        st.session_state.history = MessageHistory()
    
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

    # File upload section
    st.header("Upload Documents")
    jd_file = st.file_uploader("Upload Job Description (TXT)", type=['txt'])
    resume_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])

    if jd_file and resume_file:
        # Save uploaded files temporarily
        with open("temp_jd.txt", "wb") as f:
            f.write(jd_file.getvalue())
        with open("temp_resume.pdf", "wb") as f:
            f.write(resume_file.getvalue())

        jd_tool = TXTSearchTool("temp_jd.txt")
        resume_tool = PDFSearchTool("temp_resume.pdf")

        if not st.session_state.interview_started:
            if st.button("Start Interview"):
                with st.spinner("Generating interview questions..."):
                    interviewer_agent = create_interviewer_agent(jd_tool, resume_tool)
                    interview_task = Task(
                        description="Analyze the job description and candidate's resume. Formulate 10-12 well-structured questions.",
                        agent=interviewer_agent,
                        expected_output="A structured file containing the questions only.",
                        tools=[jd_tool, resume_tool]
                    )
                    crew1 = Crew(
                        agents=[interviewer_agent],
                        tasks=[interview_task],
                        memory=True
                    )
                    st.session_state.questions = crew1.kickoff({})
                    st.session_state.interview_started = True

        if st.session_state.interview_started:
            st.header("Interview In Progress")
            
            # Display chat history
            for message in st.session_state.history.show_history():
                role = "🤖 AI" if message['role'] == 'assistant' else "👤 You"
                st.write(f"{role}: {message['content']}")

            # Input for user responses
            user_response = st.text_area("Your response:")
            if st.button("Send"):
                if user_response:
                    llm = initialize_llm()
                    chain = create_chat_chain(llm, st.session_state.questions, st.session_state.history)
                    with st.spinner("Processing response..."):
                        ai_response = chain.invoke({
                            "question_set": st.session_state.questions,
                            "answer": user_response,
                            "chat_history": st.session_state.history.l1
                        })
                        st.session_state.history.add(user_response, ai_response.content)
                        
                        if "Thank You" in ai_response.content:
                            st.session_state.analysis_complete = True

            if st.session_state.analysis_complete:
                if st.button("Generate Analysis"):
                    with st.spinner("Analyzing interview..."):
                        analysis_agent = create_analysis_agent(jd_tool, resume_tool)
                        analysis_task = Task(
                            description="Analyze the interview script to assess the candidate's fit for the role.",
                            agent=analysis_agent,
                            expected_output="A detailed report assessing the candidate's suitability.",
                            tools=[jd_tool, resume_tool]
                        )
                        crew2 = Crew(
                            agents=[analysis_agent],
                            tasks=[analysis_task],
                            memory=True
                        )
                        analysis = crew2.kickoff({"interview_script": st.session_state.history.l1})
                        st.markdown("### Analysis Report")
                        st.write(analysis)

    # Cleanup temporary files
    if os.path.exists("temp_jd.txt"):
        os.remove("temp_jd.txt")
    if os.path.exists("temp_resume.pdf"):
        os.remove("temp_resume.pdf")

if __name__ == "__main__":
    main()
