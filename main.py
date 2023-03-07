import easyocr
import streamlit as st
import mysql.connector as connector
import pandas as pd
import re

st.title("BizCardX")
st.subheader("Extracting Business Card Data with OCR")

img = st.file_uploader("Upload Business Card")

if img is not None:
    reader = easyocr.Reader(['en'])
    result = reader.readtext(img.name, detail=0)


def get_dataframe(lst):
    df = pd.DataFrame(
        columns=['Company_Name', 'Card_Holder', 'Designation', 'Phone_Number', 'Alternate_Phone', 'Email_id',
                 'Website_URL', 'Area', 'City', 'State', 'Pincode'])
    name = lst[0]
    designation = lst[1]
    lst.remove(designation)
    lst.remove(name)
    df.loc[0, 'Card_Holder'] = name
    df.loc[0, 'Designation'] = designation

    matches_num = []
    for i in lst:
        num_pattern = '.+-[0-9]+-.+'
        matches = re.findall(num_pattern, i)

        if matches:
            matches_num.append(i)

    if len(matches_num) == 1:
        df.loc[0, 'Phone_Number'] = matches_num[0]
        lst.remove(matches_num[0])
    else:
        df.loc[0, 'Phone_Number'] = matches_num[0]
        df.loc[0, 'Alternate_Phone'] = matches_num[1]
        lst.remove(matches_num[0])
        lst.remove(matches_num[1])

    matches_email = []
    for i in lst:
        email_pattern = '.+@.+'
        matches = re.findall(email_pattern, i)

        if matches:
            matches_email.append(i)

    df.loc[0, 'Email_id'] = matches_email[0]
    lst.remove(matches_email[0])

    matches_url = []
    for i in lst:
        url_pattern = '.+.([a-zA-Z]+.com)'
        matches = re.findall(url_pattern, i)

        if matches:
            matches_url.append(i)

    lst.remove(matches_url[0])
    if 'WWW' in lst:
        df.loc[0, 'Website_URL'] = 'www.' + matches_url[0]
        lst.remove('WWW')
    else:
        df.loc[0, 'Website_URL'] = 'www.' + matches_url[0][4:]

    area1, area2 = "", ""
    matches_area = []
    for i in lst:
        area_pattern = '[0-9]+ [a-zA-Z]+'
        matches = re.findall(area_pattern, i)
        if matches:
            area1 = i
            matches_area.append(matches[0])

    df.loc[0, 'Area'] = matches_area[0] + ' St.'

    matches_city = []
    for i in lst:
        city_pattern = '.+St , ([a-zA-Z]+).+'
        matches = re.findall(city_pattern, i)
        if matches:
            matches_city.append(matches[0])

    matches_city2 = []
    for i in lst:
        city_pattern = '.+St,, ([a-zA-Z]+).+'
        matches = re.findall(city_pattern, i)
        if matches:
            matches_city2.append(matches[0])

    if matches_city:
        df.loc[0, 'City'] = matches_city[0]
    elif matches_city2:
        df.loc[0, 'City'] = matches_city2[0]
    else:
        df.loc[0, 'City'] = lst[1][:-1]
        lst.remove(lst[1])

    matches_state = []
    for i in lst:
        state_pattern2 = '([a-zA-Z]+) [0-9]+'
        matches2 = re.findall(state_pattern2, i)
        if matches2:
            area2 = i
            matches_state.append(matches2[0])

    if matches_state:
        df.loc[0, 'State'] = matches_state[0]
    else:
        matches_state = []
        for i in lst:
            state_pattern = '.+; ([a-zA-Z]+),'
            matches = re.findall(state_pattern, i)
            if matches:
                matches_state.append(matches[0])

        if matches_state:
            df.loc[0, 'State'] = matches_state[0]
        else:
            for i in lst:
                state_pattern = '.+, ([a-zA-Z]+);'
                matches = re.findall(state_pattern, i)
                if matches:
                    matches_state.append(matches[0])
            df.loc[0, 'State'] = matches_state[0]

    matches_pincode = []
    for i in lst:
        pin_pattern = '[0-9]{6}'
        matches = re.findall(pin_pattern, i)
        if matches:
            matches_pincode.append(matches[0])

    lst.remove(area1)
    if area2 in lst:
        lst.remove(area2)

    df.loc[0, 'Pincode'] = matches_pincode[0]

    if matches_pincode[0] in lst:
        lst.remove(matches_pincode[0])

    if len(lst) > 1:
        df.loc[0, 'Company_Name'] = lst[0] + ' ' + lst[1]
    else:
        df.loc[0, 'Company_Name'] = lst[0]

    return df


def upload_data(df, img):
    mydb = connector.connect(
        host="localhost",
        user="root",
        password="Ferrari488Pi!",
        database="BizCardX"
    )

    cursor1 = mydb.cursor()
    sql = "INSERT INTO card_details values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = (str(df.loc[0, "Company_Name"]), str(df.loc[0, 'Card_Holder']), str(df.loc[0, 'Designation']),
           str(df.loc[0, 'Phone_Number']), str(df.loc[0, 'Alternate_Phone']), str(df.loc[0, 'Email_id']),
           str(df.loc[0, 'Website_URL']), str(df.loc[0, 'Area']), str(df.loc[0, 'City']), str(df.loc[0, 'State']),
           str(df.loc[0, 'Pincode']), img)
    cursor1.execute(sql, val)

    mydb.commit()

    print(cursor1.rowcount, "record inserted.")


try:
    df = get_dataframe(result)
    st.dataframe(df)

    if st.button('Upload to Database'):
        upload_data(df, img.name)
        st.success("Card details uploaded to Database.")
except NameError:
    pass
