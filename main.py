import streamlit as st
import datetime
import requests
from bs4 import BeautifulSoup
from soupsieve import select_one
from collections import defaultdict
from time import sleep
import os
import pandas as pd
from fpdf import FPDF
import tempfile
from PIL import Image

def generate_pdf(df):

    today = datetime.date.today()
    # Create an instance of FPDF
    pdf = FPDF()

    # Add a page
    pdf.add_page()

    # Set the font and size
    pdf.set_font('Arial', 'B', 10)
    # Add the table header
    pdf.cell(10, 10, "Data", 1)
    pdf.cell(30, 10, "Orario", 1)
    pdf.cell(60, 10, "Corso", 1)
    pdf.cell(0, 10, "Aula", 1, 0, "C")
    pdf.set_font('Arial', '', 10)
    pdf.ln()

    # Initialize the variables 
    prev_day = None
    prev_month = None


    # Add the table data
    for i, row in df.iterrows():
        # Get the day, month, start time, and end time from the row
        day = i[0]
        month = i[1]
        start = row["inizio"]
        end = row["fine"]
        title = row["corso"]
        pdf.set_text_color(0, 0, 0)

        partial_overlap = False
        full_overlap = False

        # Filtered dataframe of lections occurring that day
        df_filtered = df.loc[(df.index.get_level_values(0) == day) & (df.index.get_level_values(1) == month)]

        
        # Iterate through the rows of the filtered DataFrame
        for j, row1 in df_filtered.iterrows():
            # Check if there is a partial overlap
            if ((row1["inizio"] <= start < row1["fine"]) or (row1["inizio"] < end <= row1["fine"])) and (row1["corso"] != title):
                partial_overlap = True
            # Check if there is a full overlap
            if (row1["inizio"] <= start and row1["fine"] >= end) and (row1["corso"] != title):
                full_overlap = True
                break

        # Truncate the text in the "aula" and "corso" columns if necessary
        if len(row["aula"]) > 40:
            aula = row["aula"][:37] + "..."
        else:
            aula = row["aula"]

        if len(row["corso"]) > 40:
            corso = row["corso"][:37] + "..."
        else:
            corso = row["corso"]

        # If the current day is different from the previous day, add a blank row
        if day != prev_day and prev_day != None:
            pdf.set_fill_color(255, 255, 255)
            pdf.cell(10, 10, "", 1, 0, "", 1)
            pdf.cell(30, 10, "", 1, 0, "", 1)
            pdf.cell(60, 10, "", 1, 0, "", 1)
            pdf.cell(0, 10, "", 1, 0, "C", 1)
            pdf.ln()
            pdf.set_fill_color(255, 255, 255)

        if prev_day is not None:
                # Get the day of the week for the current day
                current_weekday = datetime.date(today.year, month, day).weekday()
                # Get the day of the week for the previous day
                prev_weekday = datetime.date(today.year, prev_month, prev_day).weekday()
                # If the current day is in a different week from the previous day, add a black row
                if current_weekday < prev_weekday:
                    pdf.set_fill_color(0, 0, 0)
                    pdf.cell(10, 10, "", 1, 0, "", 1)
                    pdf.cell(30, 10, "", 1, 0, "", 1)
                    pdf.cell(60, 10, "", 1, 0, "", 1)
                    pdf.cell(0, 10, "", 1, 0, "C", 1)
                    pdf.ln()
                    # Reset the fill color
                    pdf.set_fill_color(255, 255, 255)


        # Format the day and month as a string and the start and end times as a single string
        data = f"{day}/{month}"
        orario = f"{start}-{end}"
        # Add the day, month, start time, and end time to the PDF
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(10, 10, data, 1)
        pdf.set_font('Arial', '', 10)

        if partial_overlap is True and full_overlap is False:
            pdf.set_text_color(255, 102, 0)
        elif full_overlap is True:
            pdf.set_text_color(250, 10, 0)
        else:
            pdf.set_text_color(0, 0, 0)

        pdf.cell(30, 10, orario, 1)
        pdf.cell(60, 10, corso, 1)
        pdf.cell(0, 10, aula, 1, 0, "C")

        pdf.ln()

        # Update the previous day variable
        prev_day = day
        prev_month = month

    # Return the pdf
    return pdf






def create_calendar(links):

    # create a dictionary to store the lections by date
    calendar = defaultdict(list)

    ## class and list for lections, links list
    class Lection:
        "lection class with lection data"
        def __init__(self, day, month, start, end, place):
            self.day = day
            self.month = month
            self.start = start
            self.end = end
            self.place = place

    lections = []
    i = 0
    errorlink = "Questo corso"
    ## get date
    today = datetime.date.today()

    ## dictionary for months manipulation
    Months_dic = {'gen': 1, 'feb' : 2, 'mar' : 3, 'apr' : 4, 'mag' : 5, 'giu' : 6, 'lug' : 7, 'ago' : 8, 'set' : 9, 'ott' : 10, 'nov' : 11, 'dic' : 12}

    placeholder0 = st.empty()
    placeholder0.text(f"Inizio a scaricare i corsi...")
    ## iterate through the links and do stuff
    for link in links:
        ##clear the lections list
        lections = []   
        ## get the webpage
        try: 
            r = requests.get(link)

        except requests.exceptions.RequestException as e:
        # handle exceptions here
            st.write(e)
            exit()

        else:
            ## get the html into soup, get the timetable of the lections
            soup = BeautifulSoup(r.content, 'html.parser')
            timetable = soup.find(id = "timetable")
            if timetable is None:
                placeholder0 = st.empty()
                placeholder1 = st.empty()
                placeholder0.text("Un corso non ha orari. Hai selezionato l'anno giusto?")
                placeholder1.text("Riprovo...")
                sleep(3)
                placeholder0.empty()
                placeholder1.empty()

                r = requests.get(link)
                soup = BeautifulSoup(r.content, 'html.parser')
                timetable = soup.find(id = "timetable")
                if timetable is None:
                    placeholder0.empty()
                    placeholder1.text("Continuo a non trovare orari per questo corso. Ricontrolla il link e riprova. Potrebbero esserci problemi di connessione al sito di uniMC oppure potresti aver messo dei link sbagliati, o non separandoli da un a capo")
                    exit()



            lections_raw = timetable.find_all("li")
            if len(timetable.select('h1 > span')) < 2:
                st.markdown(f"<a href='{link}'>{errorlink}</a> non ha orari e di conseguenza non sarà presente nel calendario. Riprova tra qualche giorno.", unsafe_allow_html=True)
                continue
            title = timetable.select('h1 > span')[1].get_text(strip=True)[13:] ## the splice removes academic year and blank spaces


            ## iterate through lections to scrape data
            for lection_raw in lections_raw:
                ## get and strip single elements of lection
                day = int(lection_raw.find(class_ = "day-number").text.strip())
                month = int(Months_dic.get(lection_raw.find(class_ = "month").text.strip()))
                time = lection_raw.find(class_ = "time").text.strip()
                place = lection_raw.find(class_ = "place").text.strip()

                ## split start and end hours
                start = time[ 0 : 5]
                end = time[-5:]
                ## if lections arent expired, append them to the calendar
                if ((today.month == month) and (today.day <= day)) or (today.month < month):
                    calendar[(day, month)].append((start, end, title, place))
            i+= 1
            if i == 1:   
                placeholder0.text(f"{i} corso scaricato...")
            else:
                placeholder0.text(f"{i} corsi scaricati...")
            sleep(0.2)

    ## if no lections are scraped, exit the program
    if not calendar:
        placeholder0.text("I corsi selezionati non hanno piu' lezioni.")
        exit()
    
    placeholder0.empty()
    # Create a Pandas DataFrame from the dictionary
    # Create an empty list to store the lection data
    lection_data = []

    # Iterate through the calendar dictionary and append the lection data to the list
    for key, value in calendar.items():
        for lection in value:
            day, month, start, end, title, place = key[0], key[1], lection[0], lection[1], lection[2], lection[3]
            lection_data.append([day, month, start, end, title, place])

    # Create the dataframe from the lection data list
    df = pd.DataFrame(lection_data, columns=['day', 'month', 'inizio', 'fine', 'corso', 'aula'])

    # Set the day and month columns as integers
    df[['day', 'month']] = df[['day', 'month']].astype(int)

    # Set the index of the dataframe to be the day and month columns
    df.set_index(['day', 'month'], inplace=True)

    # Sort the dataframe by month, day, start time, and end time
    df.sort_values(by=['month', 'day', 'inizio', 'fine'], inplace=True)

    pdf = generate_pdf(df)
    st.download_button(label = "Scarica il calendario",data = pdf.output(dest='S').encode('latin-1'), file_name = "calendarioUnimc.pdf", mime = "application/octet-stream")


    # Display the DataFrame using the st.table function
    st.table(df)




def main():
    ig_text = "Instagram"
    ig_url = "https://www.instagram.com/jump_ieri/"
    email_text = "mail"
    email_url = "mailto:e.giampieri3@studenti.unimc.it"
    editpad_url = "https://www.editpad.org/it"
    editpad_text = "Editpad"
    image0 = Image.open('sample.jpg')
    image1 = Image.open('sample1.jpg')
    title = "Calendario Modulare UniMC"

    links_edited = 1
    links = []

    st.markdown(f"<h1 style='text-align: center'>{title}</h1>", unsafe_allow_html=True)

    st.header("Cos'è?")
    st.write("Questa web app nasce dalla frustrazione di dover continuamente controllare ogni singola pagina dei corsi dell'Università di Macerata per vedere date, orari, aulee ed eventuali spostamenti. Caricando un semplice file di testo contenente tutti i corsi che segui in questo semestre, la web app crea un calendario personalizzato con i tuoi corsi e ti permette di scaricarlo in formato PDF. Come puoi vedere, vengono evidenziate anche le eventuali sovrapposizioni tra corsi.")
    st.image(image1, caption='Esempio di PDF che potrai scaricare')

    st.header("Istruzioni")
    st.write("Crea un file di testo (.txt) sul telefono/computer e copiaci i link ai corsi che intendi seguire, ad esempio:")

    
    st.image(image0, caption='Esempio di file di testo')
    st.markdown(f"Puoi utilizzare <a href='{editpad_url}'>{editpad_text}</a> per creare un file di testo direttamente da telefono. Clicca sul link, clicca su 'Create New Text Note', incolla i link andando a capo ogni volta ed infine clicca su 'Scarica e salva' in basso a sinistra. Ovviamente, a meno che tu non decida di cambiare qualche corso, basta creare il file di testo una sola volta e caricare sempre lo stesso ogni volta che decidi di aggiornare il tuo calendario. ", unsafe_allow_html=True)

    st.write("Non c'è un limite al numero di corsi che puoi aggiungere.")
    st.write("Fai attenzione a selezionare l'anno corretto del corso.")
    st.write("Fai attenzione a selezionare solo corsi appartenenti al semestre corrente e il cui calendario è stato pubblicato.")
    st.write("Fai attenzione a separare ogni corso andando a capo.")
    st.write("Una volta creato il file di testo scorri in fondo alla pagina, clicca su 'browse files', seleziona il file ed attendi qualche secondo.")
    st.write("")

    st.header("Avvertenze")
    st.write("Il calendario, sia web che PDF, viene creato aggiungendo solo le lezioni che non sono ancora avvenute. Non saranno quindi stampate le lezioni precedenti alla data in cui generi il PDF.")
    st.write("Nel PDF, una linea bianca separa i giorni, mentre una linea nera separa le settimane. Una lezione rossa si sovrappone totalmente con un'altra mentre una lezione arancione si sovrappone solo parzialmente.")
    st.write("Consiglio di aggiornare periodicamente il calendario per rimanere al passo con eventuali lezioni cancellate e/o spostate.")
    st.write("La velocità del programma dipende dall'hosting di questo sito. Più avanti potrei spostare la web app su un sito migliore.")
    st.write("")

    st.header("Contatti")
    st.markdown(f"Per segnalare eventuali bug o altro, contattami mandandomi una <a href='{email_url}'>{email_text}</a> oppure scrivendomi su <a href='{ig_url}'>{ig_text}</a>.", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Scegli un file di testo", type="txt")


    ## get links from text file, edit them to get the timetable URL
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(mode="w+b") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file.seek(0)
            with open(temp_file.name, "r") as openfileobj:
                for line in openfileobj:
                    line.strip()
                    lineobj = line.split('/')
                    if len(lineobj) <= 1:
                        continue
                    if len(lineobj) < 6 or lineobj[4] != "courses":
                        st.write("c'è un problema con il link numero:")
                        st.write(links_edited)
                        exit()
                    link = lineobj[0] + '//' + lineobj[2] + '/' + lineobj[3] + '/timetable/' + lineobj[6]
                    links.append(link)
                    links_edited+=1
        
        create_calendar(links)



main()



    
