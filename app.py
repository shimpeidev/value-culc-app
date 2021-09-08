import streamlit as st
import pandas as pd
import statsmodels.api as sm
import pyrebase
import requests
import io
import placeNameDic

config = {
    'apiKey': "AIzaSyCCCp_M76koCjxJ3KQZUg96qZtYPG6ZXCM",
    'authDomain': "staticapp-10d52.firebaseapp.com",
    'databaseURL': "https://staticapp-10d52.firebaseio.com",
    'projectId': "staticapp-10d52",
    'storageBucket': "staticapp-10d52.appspot.com",
    'messagingSenderId': "846706266056",
    'appId': "1:846706266056:web:76e5129f94a11c9bf73afd",
    'measurementId': "G-P7HBFNEMLW"
}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()


st.title('不動産価値シミュレーション')
st.text('本シミュレーションは統計的計算により算出された予測値です。実態と異なる場合があることを予めご了承のうえご使用ください。')

placeName = placeNameDic.placeNameDic
placeNameTokyo = placeNameDic.placeNameTokyoDic
placeNameKanagawa = placeNameDic.placeNameKanagawaDic
placeNameSaitama = placeNameDic.placeNameSaitamaDic
placeNameChiba = placeNameDic.placeNameChibaDic

place = st.selectbox('不動産の都道府県を選択してください',placeName)

if place == '東京都':
    place2 = st.selectbox('物件の市区町村を選択してください',placeNameTokyo)
    if place2 == '':
        st.write('')
    else:
        selected = st.selectbox('住宅分類を選択',['','中古マンション等','宅地(土地と建物)'])
        if selected == '':
            st.write('')
        else:
            placeFile = place + place2 + '.csv'
elif place == '神奈川県':
    place2 = st.selectbox('物件の市区町村を選択してください',placeNameKanagawa)
    if place2 == '':
        st.write('')
    else:
        selected = st.selectbox('住宅分類を選択',['','中古マンション等','宅地(土地と建物)'])
        if selected == '':
            st.write('')
        else:
            placeFile = place + place2 + '.csv'
elif place == '埼玉県':
    place2 = st.selectbox('物件の市区町村を選択してください',placeNameSaitama)
    if place2 == '':
        st.write('')
    else:
        selected = st.selectbox('住宅分類を選択',['','中古マンション等','宅地(土地と建物)'])
        if selected == '':
            st.write('')
        else:
            placeFile = place + place2 + '.csv'

elif place == '千葉県':
    place2 = st.selectbox('物件の市区町村を選択してください',placeNameChiba)
    if place2 == '':
        st.write('')
    else:
        selected = st.selectbox('住宅分類を選択',['','中古マンション等','宅地(土地と建物)'])
        if selected == '':
            st.write('')
        else:
            placeFile = place + place2 + '.csv'

elif place == '対象地区がない':
    st.write('https://www.land.mlit.go.jp/webland/download.html')
    uploaded_file = st.file_uploader("上のサイトからファイルをダウンロードして、こちらへアップロード",type='csv')
else:
    st.write('')

if place == '':
    st.write('')
elif place == '対象地区がない':
    if uploaded_file is None:
        st.write('')
    else:
        selected = st.selectbox('住宅分類を選択',['','中古マンション等','宅地(土地と建物)'])
        if selected == '':
            st.write('')
        else:
            placeFile = uploaded_file
            df = pd.read_csv(placeFile,encoding = 'cp932')

            df = df[['取引時点','種類','最寄駅：距離（分）','面積（㎡）','建築年','取引価格（総額）']]
            df = df[df['種類'].isin([selected])]
            df['取引年'] = df['取引時点'].str[:4].astype(int)
            df['年度'] = df['取引時点'].str[:5]

            df = df.dropna(subset=['建築年'])
            df['年号'] = df['建築年'].str[:2]
            df['和暦_年'] = df['建築年'].str[2:].str.replace('年','')
            df = df[df['和暦_年'] != '']
            df['和暦_年'] = df['和暦_年'].astype(int)
            df.loc[df['年号']=='昭和','西暦_年'] = df['和暦_年'] + 1925
            df.loc[df['年号']=='平成','西暦_年'] = df['和暦_年'] + 1988
            df.loc[df['年号']=='令和','西暦_年'] = df['和暦_年'] + 2018
            df['西暦_年'] = df['西暦_年'].astype(int)
            df['築年数'] = 2021-df['西暦_年']

            df['面積'] = pd.to_numeric(df['面積（㎡）'], errors='coerce')
            df = df.dropna(subset = ['面積'])
            df['面積'] = df['面積'].astype(int)
            # #距離をintへ
            df = df.dropna(subset=['最寄駅：距離（分）'])
            df['徒歩'] = pd.to_numeric(df['最寄駅：距離（分）'], errors='coerce')
            df = df.dropna(subset = ['徒歩'])
            df['徒歩'] = df['徒歩'].astype(int)

            if st.checkbox('対象地域の価格推移を表示'):
                chart_data = df['取引価格（総額）'].groupby(df['年度']).mean()
                st.line_chart(chart_data)

            # if data_range == 0:
            #     st.write('')
            # else:

            rangeAge = st.slider("サンプリングするデータの期間を設定（年前まで）",max_value=15,value=1)
            df = df[df['取引年'] >= 2020-rangeAge]
            # chart_data = df['取引価格（総額）'].groupby(df['年度']).mean()
            # st.line_chart(chart_data)
            

            x_name = ['築年数','徒歩','面積']
            x = df[x_name]
            y = df['取引価格（総額）']

            model = sm.OLS(y,sm.add_constant(x))
            result = model.fit()
            summary = result.summary()

            rsquared = result.rsquared *100
            rsquared = rsquared.astype(int)

            def culc():
                global res
                df_predict = pd.DataFrame({'築年数':age,'徒歩':walk_dis,'面積':squ_meta})
                df_predict['築年数'] = df_predict['築年数'].astype(int)
                df_predict['徒歩'] = df_predict['徒歩'].astype(int)
                df_predict['面積'] = df_predict['面積'].astype(int)
                df_predict = df_predict.append({'築年数': 0, '徒歩': 0, '面積': 0}, ignore_index=True)
                res = result.predict(sm.add_constant(df_predict[x_name])).astype(int)
                return res[0]

            with st.form("my_form"):
                st.text('価値を算出したい不動産のスペックを設定')
                age = st.slider("築年数を設定（年）",max_value=50)
                age = pd.Series(age)
                walk_dis = st.slider('最寄駅からの徒歩時間を設定（分）',max_value=50)
                walk_dis = pd.Series(walk_dis)
                squ_meta = st.slider('平米数を設定（m2）',max_value=200)
                squ_meta = pd.Series(squ_meta)
                st.write('決定係数(信頼度合):',rsquared,'%')
                st.write('サンプル数:',len(df),'件')
                st.text('*決定係数が高ければ信頼度が高いモデル')
                st.line_chart(chart_data)

                button = st.form_submit_button('不動産価値を算出',on_click=culc)

                finalPrice = culc()
                finalPriceDisp = "{:,}".format(finalPrice) + '円'

                if button == False:
                    st.write('')
                else:
                    if finalPrice < 0:
                        st.write('不動産価値を算出できません。値を再設定してください。')
                    else:
                        st.metric(label="不動産価値",value=finalPriceDisp)

            with st.form("my_form2"):
                st.text('収支計算')
                payPrice = st.number_input('販売・購入価格（万円）',value=0)
                payPrice = payPrice *10000
                feePrice1 = st.number_input('管理費(円)',value=0)
                feePrice2 = st.number_input('修繕積立金（円）',value=0)
                bonusPayBuck = st.selectbox('ボーナス月の倍率（倍）',(1,2,3,4,5,6,7,8,9,10))
                loanspan = st.slider("ローン年数（年）",max_value=35)
                interestRate = st.number_input('金利（%）',value=0.65)
                sellTime = st.slider("売却時期（年後）",max_value=50)
                if st.form_submit_button('収支を計算'):
                    yearPayPrice = payPrice / loanspan /12
                    nowPrice = payPrice
                    total = 0
                    for i in range(-1,loanspan*12,1):
                        i += 1
                        nowPrice = nowPrice - yearPayPrice
                        interest = nowPrice * interestRate/12 /100
                        total += interest
                    totalPrice = payPrice + total
                    payMonth = totalPrice /loanspan / (10 + 2 * bonusPayBuck) + total/loanspan/12
                    payBonus = payMonth * bonusPayBuck
                    payMonth2 = payMonth + feePrice1 + feePrice2
                    payBonus2 = payBonus + feePrice1 + feePrice2


                    df_predict2 = pd.DataFrame({'築年数':sellTime,'徒歩':walk_dis,'面積':squ_meta})
                    df_predict2['築年数'] = df_predict2['築年数'].astype(int)
                    df_predict2['徒歩'] = df_predict2['徒歩'].astype(int)
                    df_predict2['面積'] = df_predict2['面積'].astype(int)
                    df_predict2 = df_predict2.append({'築年数': 0, '徒歩': 0, '面積': 0}, ignore_index=True)
                    res2 = result.predict(sm.add_constant(df_predict2[x_name])).astype(int)
                    sellAblePrice = res2[0]

                    bop = sellAblePrice - totalPrice
                    red = (bop / sellTime / 12) * -1 + feePrice1 + feePrice2


                    totalPrice = int(totalPrice)
                    totalPrice = "{:,}".format(totalPrice) + '円'
                    payMonth = int(payMonth)
                    payMonth = "{:,}".format(payMonth) + '円'
                    payBonus = int(payBonus)
                    payBonus = "{:,}".format(payBonus) + '円'
                    payMonth2 = int(payMonth2)
                    payMonth2 = "{:,}".format(payMonth2) + '円'
                    payBonus2 = int(payBonus2)
                    payBonus2 = "{:,}".format(payBonus2) + '円'
                    sellAblePrice = int(sellAblePrice)
                    sellAblePrice = "{:,}".format(sellAblePrice) + '円'
                    bop = int(bop)
                    bop = "{:,}".format(bop) + '円'
                    red = int(red)
                    red = "{:,}".format(red) + '円'

                    st.metric(label="費用総額",value=totalPrice)
                    st.metric(label="返済額（月）",value=payMonth)
                    st.metric(label="返済額（ボーナス月）",value=payBonus)
                    st.metric(label="支払額（月）",value=payMonth2)
                    st.metric(label="支払額（ボーナス月）",value=payBonus2)
                    st.metric(label="売却見込価格",value=sellAblePrice)
                    st.metric(label="収支結果",value=bop)
                    st.metric(label="費用（月）*",value=red)
                    st.text('*資産減産額（月）＋　管理費・修繕積立金で算出。賃貸（家賃）との比較に有効')
else:
    if place2 == '':
        st.write('')
    else:
        if selected == '':
            st.write('')
        else:
            URL = storage.child(placeFile).get_url(placeFile)
            r = requests.get(URL).content
            df = pd.read_csv(io.BytesIO(r),encoding = 'cp932')


            df = df[['取引時点','種類','最寄駅：距離（分）','面積（㎡）','建築年','取引価格（総額）']]
            df = df[df['種類'].isin([selected])]
            df['取引年'] = df['取引時点'].str[:4].astype(int)
            df['年度'] = df['取引時点'].str[:5]

            df = df.dropna(subset=['建築年'])
            df['年号'] = df['建築年'].str[:2]
            df['和暦_年'] = df['建築年'].str[2:].str.replace('年','')
            df = df[df['和暦_年'] != '']
            df['和暦_年'] = df['和暦_年'].astype(int)
            df.loc[df['年号']=='昭和','西暦_年'] = df['和暦_年'] + 1925
            df.loc[df['年号']=='平成','西暦_年'] = df['和暦_年'] + 1988
            df.loc[df['年号']=='令和','西暦_年'] = df['和暦_年'] + 2018
            df['西暦_年'] = df['西暦_年'].astype(int)
            df['築年数'] = 2021-df['西暦_年']

            df['面積'] = pd.to_numeric(df['面積（㎡）'], errors='coerce')
            df = df.dropna(subset = ['面積'])
            df['面積'] = df['面積'].astype(int)
            # #距離をintへ
            df = df.dropna(subset=['最寄駅：距離（分）'])
            df['徒歩'] = pd.to_numeric(df['最寄駅：距離（分）'], errors='coerce')
            df = df.dropna(subset = ['徒歩'])
            df['徒歩'] = df['徒歩'].astype(int)

            if st.checkbox('対象地域の価格推移を表示'):
                chart_data = df['取引価格（総額）'].groupby(df['年度']).mean()
                st.line_chart(chart_data)

            # if data_range == 0:
            #     st.write('')
            # else:
            rangeAge = st.slider("サンプリングするデータの期間を設定（年前まで）",max_value=15,value=1)
            df = df[df['取引年'] >= 2020-rangeAge]
            # chart_data = df['取引価格（総額）'].groupby(df['年度']).mean()
            # st.line_chart(chart_data)

            x_name = ['築年数','徒歩','面積']
            x = df[x_name]
            y = df['取引価格（総額）']

            model = sm.OLS(y,sm.add_constant(x))
            result = model.fit()
            summary = result.summary()

            rsquared = result.rsquared *100
            rsquared = rsquared.astype(int)

                



            def culc():
                global res
                df_predict = pd.DataFrame({'築年数':age,'徒歩':walk_dis,'面積':squ_meta})
                df_predict['築年数'] = df_predict['築年数'].astype(int)
                df_predict['徒歩'] = df_predict['徒歩'].astype(int)
                df_predict['面積'] = df_predict['面積'].astype(int)
                df_predict = df_predict.append({'築年数': 0, '徒歩': 0, '面積': 0}, ignore_index=True)
                res = result.predict(sm.add_constant(df_predict[x_name])).astype(int)
                return res[0]

            with st.form("my_form"):
                st.text('価値を算出したい不動産のスペックを設定')
                age = st.slider("築年数を設定（年）",max_value=50)
                age = pd.Series(age)
                walk_dis = st.slider('最寄駅からの徒歩時間を設定（分）',max_value=50)
                walk_dis = pd.Series(walk_dis)
                squ_meta = st.slider('平米数を設定（m2）',max_value=200)
                squ_meta = pd.Series(squ_meta)
                st.write('決定係数(信頼度合):',rsquared,'%')
                st.write('サンプル数:',len(df),'件')
                st.text('*決定係数が高ければ信頼度が高いモデル')
                button = st.form_submit_button('不動産価値を算出',on_click=culc)


                finalPrice = culc()
                finalPriceDisp = "{:,}".format(finalPrice) + '円'

                if button == False:
                    st.write('')
                else:
                    if finalPrice < 0:
                        st.write('不動産価値を算出できません。値を再設定してください。')
                    else:
                        st.metric(label="不動産価値",value=finalPriceDisp)



            with st.form("my_form2"):
                st.text('収支計算')
                payPrice = st.number_input('販売・購入価格（万円）',value=0)
                payPrice = payPrice *10000
                feePrice1 = st.number_input('管理費(円)',value=0)
                feePrice2 = st.number_input('修繕積立金（円）',value=0)
                bonusPayBuck = st.selectbox('ボーナス月の倍率（倍）',(1,2,3,4,5,6,7,8,9,10))
                loanspan = st.slider("ローン年数（年）",max_value=35)
                interestRate = st.number_input('金利（%）',value=0.65)
                sellTime = st.slider("売却時期（年後）",max_value=50)
                if st.form_submit_button('収支を計算'):
                    yearPayPrice = payPrice / loanspan /12
                    nowPrice = payPrice
                    total = 0
                    for i in range(-1,loanspan*12,1):
                        i += 1
                        nowPrice = nowPrice - yearPayPrice
                        interest = nowPrice * interestRate/12 /100
                        total += interest
                    totalPrice = payPrice + total
                    payMonth = totalPrice /loanspan / (10 + 2 * bonusPayBuck) + total/loanspan/12
                    payBonus = payMonth * bonusPayBuck
                    payMonth2 = payMonth + feePrice1 + feePrice2
                    payBonus2 = payBonus + feePrice1 + feePrice2


                    df_predict2 = pd.DataFrame({'築年数':sellTime,'徒歩':walk_dis,'面積':squ_meta})
                    df_predict2['築年数'] = df_predict2['築年数'].astype(int)
                    df_predict2['徒歩'] = df_predict2['徒歩'].astype(int)
                    df_predict2['面積'] = df_predict2['面積'].astype(int)
                    df_predict2 = df_predict2.append({'築年数': 0, '徒歩': 0, '面積': 0}, ignore_index=True)
                    res2 = result.predict(sm.add_constant(df_predict2[x_name])).astype(int)
                    sellAblePrice = res2[0]

                    bop = sellAblePrice - totalPrice
                    red = (bop / sellTime / 12) * -1 + feePrice1 + feePrice2


                    totalPrice = int(totalPrice)
                    totalPrice = "{:,}".format(totalPrice) + '円'
                    payMonth = int(payMonth)
                    payMonth = "{:,}".format(payMonth) + '円'
                    payBonus = int(payBonus)
                    payBonus = "{:,}".format(payBonus) + '円'
                    payMonth2 = int(payMonth2)
                    payMonth2 = "{:,}".format(payMonth2) + '円'
                    payBonus2 = int(payBonus2)
                    payBonus2 = "{:,}".format(payBonus2) + '円'
                    sellAblePrice = int(sellAblePrice)
                    sellAblePrice = "{:,}".format(sellAblePrice) + '円'
                    bop = int(bop)
                    bop = "{:,}".format(bop) + '円'
                    red = int(red)
                    red = "{:,}".format(red) + '円'

                    st.metric(label="費用総額",value=totalPrice)
                    st.metric(label="返済額（月）",value=payMonth)
                    st.metric(label="返済額（ボーナス月）",value=payBonus)
                    st.metric(label="支払額（月）",value=payMonth2)
                    st.metric(label="支払額（ボーナス月）",value=payBonus2)
                    st.metric(label="売却見込価格",value=sellAblePrice)
                    st.metric(label="収支結果",value=bop)
                    st.metric(label="費用（月）*",value=red)
                    st.text('*資産減産額（月）＋　管理費・修繕積立金で算出。賃貸（家賃）との比較に有効')

                




        



    