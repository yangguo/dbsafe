import glob
import json
import pandas as pd
import streamlit as st
import time
from snapshot import get_chrome_driver, get_safari_driver
from selenium.webdriver.common.by import By
import random
import os
import datetime
import csv
import plotly.express as px
from collections import Counter


pensafe = "safe"
mappath = "map/chinageo.json"
temppath = "temp"

org2name = {
    "北京": "beijing",
    "厦门": "xiamen",
    "青海": "qinghai",
    "甘肃": "gansu",
    "天津": "tianjin",
    "河北": "hebei",
    "贵州": "guizhou",
    "湖南": "hunan",
    "深圳": "shenzhen",
    "江西": "jiangxi",
    "广东": "guangdong",
    "重庆": "chongqing",
    "黑龙江": "heilongjiang",
    "福建": "fujian",
    "河南": "henan",
    "陕西": "shaanxi",
    "海南": "hainan",
    "云南": "yunnan",
    "湖北": "hubei",
    "山东": "shandong",
    "新疆": "xinjiang",
    "宁波": "ningbo",
    "大连": "dalian",
    "江苏": "jiangsu",
    "内蒙古": "neimenggu",
    "浙江": "zhejiang",
    "吉林": "jilin",
    "广西": "guangxi",
    "上海": "shanghai",
    "宁夏": "ningxia",
    "安徽": "anhui",
    "山西": "shanxi",
    "青岛": "qingdao",
    "辽宁": "liaoning",
    "西藏": "xizang",
    "四川": "sichuan",
    "总部": "safe",
}

city2province = {
    "北京": "北京市",
    "厦门": "福建省",
    "青海": "青海省",
    "甘肃": "甘肃省",
    "天津": "天津市",
    "河北": "河北省",
    "贵州": "贵州省",
    "湖南": "湖南省",
    "深圳": "广东省",
    "江西": "江西省",
    "广东": "广东省",
    "重庆": "重庆市",
    "黑龙江": "黑龙江省",
    "福建": "福建省",
    "河南": "河南省",
    "陕西": "陕西省",
    "海南": "海南省",
    "云南": "云南省",
    "湖北": "湖北省",
    "山东": "山东省",
    "新疆": "新疆维吾尔自治区",
    "宁波": "浙江省",
    "大连": "辽宁省",
    "江苏": "江苏省",
    "内蒙古": "内蒙古自治区",
    "浙江": "浙江省",
    "吉林": "吉林省",
    "广西": "广西壮族自治区",
    "上海": "上海市",
    "宁夏": "宁夏回族自治区",
    "安徽": "安徽省",
    "山西": "山西省",
    "青岛": "山东省",
    "辽宁": "辽宁省",
    "西藏": "西藏自治区",
    "四川": "四川省",
    "总部": "北京市",
}

baseurl = "http://www.safe.gov.cn/www/illegal/index?page="

org2url = {
    "北京": "http://beijing.pbc.gov.cn/beijing/113682/113700/113707/10983/index",
}


def get_csvdf(penfolder, beginwith):
    files2 = glob.glob(penfolder + "**/" + beginwith + "*.csv", recursive=True)
    dflist = []
    # filelist = []
    for filepath in files2:
        pendf = pd.read_csv(filepath, index_col=0)
        dflist.append(pendf)
        # filelist.append(filename)
    if len(dflist) > 0:
        df = pd.concat(dflist)
        df.reset_index(drop=True, inplace=True)
    else:
        df = pd.DataFrame()
    return df


# @st.cache
def get_safedetail(orgname=""):
    beginwith = "safedtl"
    pendf = get_csvdf(pensafe, beginwith)
    if orgname != "":
        pendf = pendf[pendf["区域"] == orgname]
    # if not empty
    if len(pendf) > 0:
        # format date
        # pendf["发布日期"] = pd.to_datetime(pendf["date"]).dt.date
        pendf.loc[:, "发布日期"] = pendf["date"].apply(parse_date)

    return pendf


def searchsafe(
    df,
    start_date,
    end_date,
    wenhao_text,
    people_text,
    event_text,
    penalty_text,
    org_text,
    province,
    min_penalty=0,
):
    # wenhao_text = split_words(wenhao_text)
    # people_text = split_words(people_text)
    # event_text = split_words(event_text)
    # # law_text = split_words(law_text)
    # penalty_text = split_words(penalty_text)
    # org_text = split_words(org_text)

    col = [
        # "序号",
        "企业名称",
        "处罚决定书文号",
        "违法行为类型",
        "行政处罚内容",
        "作出行政处罚决定机关名称",
        "作出行政处罚决定日期",
        "备注",
        "区域",
        "link",
        "发布日期",
    ]

    searchdf = df[
        (df["发布日期"] >= start_date)
        & (df["发布日期"] <= end_date)
        & (df["违规主体名称"].str.contains(people_text))
        & (df["行政处罚决定书文号"].str.contains(wenhao_text))
        & (df["违法行为类型"].str.contains(event_text))
        & (df["处罚内容"].str.contains(penalty_text))
        & (df["作出处罚决定的行政机关名称"].str.contains(org_text))
        & (df["区域"].isin(province))
        & (df["amount"] >= min_penalty)
    ]  # [col]
    # sort by date desc
    searchdf = searchdf.sort_values(by=["发布日期"], ascending=False)
    # drop duplicates
    # searchdf.drop_duplicates(subset=["link"], inplace=True)
    # reset index
    searchdf = searchdf.reset_index(drop=True)
    return searchdf


def display_eventdetail(search_df):
    # draw plotly figure
    display_search_df(search_df)
    # get search result from session
    search_dfnew = st.session_state["search_result_safe"]
    total = len(search_dfnew)
    # st.sidebar.metric("总数:", total)
    st.markdown("### 搜索结果" + "(" + str(total) + "条)")
    # display download button
    st.download_button(
        "下载搜索结果",
        data=search_dfnew.to_csv().encode("utf_8_sig"),
        file_name="搜索结果.csv",
    )
    # display columns
    discols = [
        "发布日期",
        "行政处罚决定书文号",
        "违规主体名称",
        "违法事实",
        "区域",
        "link",
    ]
    # get display df
    display_df = search_dfnew[discols]
    # set index column using loc
    # display_df["序号"] = display_df.index
    # display_df.loc[:, "序号"] = display_df.index
    # change column name
    # display_df.columns = ["link", "文号","当事人",  "发布日期", "区域"]

    data = st.dataframe(display_df, on_select="rerun", selection_mode="single-row")

    selected_rows = data["selection"]["rows"]

    # data = df2aggrid(display_df)
    # display data
    # selected_rows = data["selected_rows"]
    if selected_rows == []:
        st.error("请先选择查看案例")
        st.stop()

    # id = selected_rows[0]["序号"]
    id = display_df.loc[selected_rows[0], "link"]
    # display event detail
    st.markdown("##### 案情经过")
    # select search_dfnew by id
    # selected_rows_df = search_dfnew[search_dfnew.index == id]
    selected_rows_df = search_dfnew[search_dfnew["link"] == id]

    # st.text(selected_rows_df.columns)

    selected_rows_df = selected_rows_df[
        [
            "行政处罚决定书文号",
            "违规主体名称",
            "法定代表人或负责人姓名",
            "注册地址",
            "统一社会信用代码",
            "作出处罚决定的行政机关名称",
            "违法行为类型",
            "违法事实",
            "处罚依据",
            "处罚类别",
            "处罚内容",
            "罚款金额（万元）",
            "没收金额（万元）",
            "处罚决定日期",
            "公开截止期",
            "备注",
            "link",
            "违法主体姓名",
            "有效身份证件号码（身份证、护照等）",
            "区域",
            "罚没款金额（万元）",
            "公示截止期",
            "发布日期",
            "amount",
        ]
    ]
    # rename column
    selected_rows_df.columns = [
        "行政处罚决定书文号",
        "违规主体名称",
        "法定代表人或负责人姓名",
        "注册地址",
        "统一社会信用代码",
        "作出处罚决定的行政机关名称",
        "违法行为类型",
        "违法事实",
        "处罚依据",
        "处罚类别",
        "处罚内容",
        "罚款金额（万元）",
        "没收金额（万元）",
        "处罚决定日期",
        "公开截止期",
        "备注",
        "链接",
        "违法主体姓名",
        "有效身份证件号码（身份证、护照等）",
        "区域",
        "罚没款金额（万元）",
        "公示截止期",
        "发布日期",
        "罚没总金额（万元）",
    ]

    # transpose and set column name
    selected_rows_df = selected_rows_df.astype(str).T

    selected_rows_df.columns = ["内容"]
    # display selected rows
    st.table(selected_rows_df)

    # get event detail url
    url = selected_rows_df.loc["链接", "内容"]
    # display url
    st.markdown("##### 案例链接")
    st.markdown(url)


# summary of pboc
def display_summary():
    # get old sumeventdf
    oldsum2 = get_safedetail("")
    # get length of old eventdf
    oldlen2 = len(oldsum2)
    # display isnull sum
    # st.write(oldsum2.isnull().sum())
    # get min and max date of old eventdf
    min_date2 = oldsum2["发布日期"].min()
    max_date2 = oldsum2["发布日期"].max()
    # use metric
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("案例总数", oldlen2)
    with col2:
        st.metric("案例日期范围", f"{min_date2} - {max_date2}")

    # sum max,min date and size by org
    sumdf2 = (
        oldsum2.groupby("区域")["发布日期"].agg(["max", "min", "count"]).reset_index()
    )
    sumdf2.columns = ["区域", "最近发文日期", "最早发文日期", "案例总数"]
    # sort by date
    sumdf2.sort_values(by=["最近发文日期"], ascending=False, inplace=True)
    # reset index
    sumdf2.reset_index(drop=True, inplace=True)
    # display
    st.markdown("#### 按区域统计")
    st.table(sumdf2)

    return sumdf2


def display_safesum(org_name_ls):
    for org_name in org_name_ls:
        st.markdown("#### " + org_name)
        st.markdown("列表")
        oldsum = get_safesum(org_name)
        display_suminfo(oldsum)
        st.markdown("详情")
        dtl = get_safedetail(org_name)
        # drop null value
        dtl = dtl.dropna(subset=["违法事实"])
        # dtl1 = dtl.drop_duplicates(subset=["name", "date", "link"])
        display_suminfo(dtl)


def get_safesum(orgname):
    # org_name_index = org2name[orgname]
    # beginwith = "pbocsum" + org_name_index
    beginwith = "safesum"
    allpendf = get_csvdf(pensafe, beginwith)
    # get pendf by orgname
    pendf = allpendf[allpendf["区域"] == orgname]
    # cols = ["name", "date", "link", "sum"]
    # if not empty
    if len(pendf) > 0:
        # copy df
        pendf = pendf.copy()
        # pendf["发布日期"] = pd.to_datetime(pendf["date"]).dt.date
        # pendf.loc[:, "发布日期"] = pd.to_datetime(pendf["date"]).dt.date
        pendf.loc[:, "发布日期"] = pendf["date"].apply(parse_date)
    return pendf


def parse_date(date_string):
    try:
        return pd.to_datetime(date_string, format="%Y/%m/%d").date()
    except ValueError:
        try:
            return pd.to_datetime(date_string, format="%Y-%m-%d").date()
        except ValueError:
            # Add more formats as needed
            return None  # or raise an exception


def display_suminfo(df):
    # get length of old eventdf
    oldlen = len(df)
    if oldlen > 0:
        # get unique link number
        linkno = df["link"].nunique()
        # get min and max date of old eventdf
        min_date = df["发布日期"].min()
        max_date = df["发布日期"].max()
        # use metric for length and date
        col1, col2, col3 = st.columns([1, 1, 1])
        # col1.metric("案例总数", oldlen)
        col1.write(f"案例总数：{oldlen}")
        col2.write(f"链接数：{linkno}")
        # col2.metric("日期范围", f"{min_date} - {max_date}")
        col3.write(f"日期范围：{min_date} - {max_date}")


# get sumeventdf in page number range
def get_sumeventdf(orgname, start, end):
    org_name_index = org2name[orgname]
    browser = get_chrome_driver(temppath)

    cityname = org_name_index

    resultls = []
    errorls = []
    count = 0
    for n in range(start, end + 1):
        st.info("page: " + str(n))
        st.info(str(count) + " begin")
        url = baseurl + str(n) + "&siteid=" + cityname
        st.info("url: " + url)
        # st.write(org_name_index)
        try:
            browser.implicitly_wait(3)
            browser.get(url)
            # wait for page load
            # time.sleep(10)
            # ls1=browser.find_elements_by_xpath('//tbody//tr/td')
            ls1 = browser.find_elements(By.XPATH, "//tbody//td")
            nols = []
            namels = []
            datels = []
            docls = []
            total = len(ls1) // 4
            for i in range(total):
                nols.append(ls1[i * 4].text)
                namels.append(ls1[i * 4 + 1].text)
                datels.append(ls1[i * 4 + 2].text)
                docls.append(ls1[i * 4 + 3].text)

            ls2 = browser.find_elements(By.XPATH, "//tbody//a")
            linkls = []
            for link in ls2:
                linkls.append(link.get_attribute("href"))
            pandf = pd.DataFrame(
                {
                    "no": nols,
                    "name": namels,
                    "date": datels,
                    "link": linkls,
                    "doc": docls,
                }
            )
            resultls.append(pandf)
            st.info("finished: " + str(n))
        except Exception as e:
            st.error("error!: " + str(e))
            errorls.append(url)

        mod = (n + 1) % 2
        if mod == 0 and count > 0:
            tempdf = pd.concat(resultls)
            savename = "tempsum-" + org_name_index + str(count + 1)
            savedf(tempdf, savename)

        wait = random.randint(2, 20)
        time.sleep(wait)
        st.info("finish: " + str(count))
        count += 1

    browser.quit()
    if len(resultls) > 0:
        sumdf = pd.concat(resultls)
        sumdf["区域"] = orgname
        savedf(sumdf, "tempsumall-" + org_name_index + str(count))
    else:
        sumdf = pd.DataFrame()

    return sumdf


def savedf(df, basename):
    savename = basename + ".csv"
    savepath = os.path.join(pensafe, savename)
    df.to_csv(savepath)


# update sumeventdf
def update_sumeventdf(currentsum, orgname):
    org_name_index = org2name[orgname]
    # get detail
    oldsum = get_safesum(orgname)
    if oldsum.empty:
        oldidls = []
    else:
        oldidls = oldsum["link"].tolist()
    currentidls = currentsum["link"].tolist()
    # print('oldidls:',oldidls)
    # print('currentidls:', currentidls)
    # get current idls not in oldidls
    newidls = [x for x in currentidls if x not in oldidls]
    # print('newidls:', newidls)
    # newidls=list(set(currentidls)-set(oldidls))
    newdf = currentsum[currentsum["link"].isin(newidls)]
    # if newdf is not empty, save it
    if newdf.empty is False:
        newdf.reset_index(drop=True, inplace=True)
        nowstr = get_now()
        savename = "safesum" + org_name_index + nowstr
        # add orgname
        newdf["区域"] = orgname
        savedf(newdf, savename)
    return newdf


def get_now():
    now = datetime.datetime.now()
    now_str = now.strftime("%Y%m%d%H%M%S")
    return now_str


def toupt_safesum(org_name_ls):
    touptls = []
    for org_name in org_name_ls:
        # st.write(org_name)
        oldsum = get_safesum(org_name)
        lensum = len(oldsum)
        dtl = get_safedetail(org_name)
        # drop null value
        dtl = dtl.dropna(subset=["违法事实"])
        lendtl = len(dtl)
        if lensum > lendtl:
            touptls.append(org_name)
    return touptls


# update toupd
def update_toupd(orgname):
    org_name_index = org2name[orgname]
    # get sumeventdf
    currentsum = get_safesum(orgname)
    # get detail
    oldsum = get_safedetail(orgname)
    # drop null value
    oldsum = oldsum.dropna(subset=["违法事实"])
    if oldsum.empty:
        oldidls = []
    else:
        # if no link column, use []
        if "link" not in oldsum.columns:
            oldidls = []
        else:
            oldidls = oldsum["link"].tolist()
    if currentsum.empty:
        currentidls = []
    else:
        currentidls = currentsum["link"].tolist()
    # get current idls not in oldidls
    newidls = [x for x in currentidls if x not in oldidls]

    if currentsum.empty:
        newdf = pd.DataFrame()
    else:
        newdf = currentsum[currentsum["link"].isin(newidls)]
    # if newdf is not empty, save it
    if newdf.empty is False:
        # sort by date desc
        newdf.sort_values(by=["date"], ascending=False, inplace=True)
        # reset index
        newdf.reset_index(drop=True, inplace=True)
        # save to update dtl list
        toupdname = "safetoupd" + org_name_index
        # add orgname
        newdf.loc[:, "区域"] = orgname
        # newdf["区域"] = orgname
        savedf(newdf, toupdname)
    return newdf


def get_safetoupd(orgname):
    org_name_index = org2name[orgname]
    beginwith = "safetoupd" + org_name_index
    pendf = get_csvdf(pensafe, beginwith)
    return pendf


# get event detail
def get_eventdetail(eventsum, orgname):
    org_name_index = org2name[orgname]
    # browser = get_chrome_driver(temppath)
    browser = get_safari_driver()
    detaills = eventsum["link"].tolist()
    datels = eventsum["date"].tolist()

    resultls = []
    errorls = []
    count = 0
    for date, durl in zip(datels, detaills):
        st.info(str(count) + " begin")
        st.info("url: " + durl)
        try:
            browser.get(durl)

            hl1 = browser.find_elements(By.XPATH, "//body//th")
            dl1 = browser.find_elements(By.XPATH, "//body//td")
            df = web2table(hl1, dl1)
            df["link"] = durl
            df["date"] = date
            resultls.append(df)

        except Exception as e:
            st.error("error!: " + str(e))
            st.error("check url:" + durl)
            errorls.append(durl)

        mod = (count + 1) % 10
        if mod == 0 and count > 0:
            # concat all result
            if resultls:
                tempdf = pd.concat(resultls)
                tempdf["区域"] = orgname
                savename = "tempdtl-" + org_name_index + str(count + 1)
                # savetemp(tempdf, savename)
                savetempsub(tempdf, savename, org_name_index)

        wait = random.randint(2, 20)
        time.sleep(wait)
        st.info("finish: " + str(count))
        count += 1

    browser.quit()
    # print errorls
    if len(errorls) > 0:
        st.error("error list:")
        st.error(errorls)
    # if resultls is not empty, save it
    if resultls:
        safedf = pd.concat(resultls)
        safedf["区域"] = orgname
        savecsv = "safedtl" + org_name_index + get_now()
        # reset index
        safedf.reset_index(drop=True, inplace=True)
        # savetemp(pbocdf, savecsv)
        savetempsub(safedf, savecsv, org_name_index)
        savedf(safedf, savecsv)
    else:
        safedf = pd.DataFrame()

    return safedf


# save df to sub folder under temp folder
def savetempsub(df, basename, subfolder):
    savename = basename + ".csv"
    savepath = os.path.join(temppath, subfolder, savename)
    # create folder if not exist
    if not os.path.exists(os.path.join(temppath, subfolder)):
        os.makedirs(os.path.join(temppath, subfolder))
    df.to_csv(savepath, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\")


def web2table(hl1, dl1):
    headls = [h.text for h in hl1]
    contls = [d.text for d in dl1]
    row_data = dict(zip(headls, contls))
    df = pd.DataFrame(row_data, index=[0])
    return df


def download_safesum():
    st.markdown("#### 案例数据下载")

    # download by org
    st.markdown("##### 按区域下载")

    sumlist = []
    dtllist = []

    for orgname in org2name.keys():
        st.markdown("##### " + orgname)
        # get orgname
        org_name_index = org2name[orgname]
        # beginwith = "pbocsum" + org_name_index
        # oldsum = get_csvdf(penpboc, beginwith)
        oldsum = get_safesum(orgname)
        lensum = len(oldsum)
        st.write("列表数据量: " + str(lensum))

        if lensum > 0:
            # get min and max date
            mindate = oldsum["date"].min()
            maxdate = oldsum["date"].max()
            st.write("列表日期: " + maxdate + " - " + mindate)
            # listname
            listname = "safesum" + org_name_index + get_now() + ".csv"
            # download list data
            st.download_button(
                "下载列表数据",
                data=oldsum.to_csv().encode("utf_8_sig"),
                file_name=listname,
            )
        # beginwith = "pbocdtl" + org_name_index
        # dtl = get_csvdf(penpboc, beginwith)
        dtl = get_safedetail(orgname)
        # drop null value
        dtl = dtl.dropna(subset=["违法事实"])
        # dtl["区域"] = orgname
        lendtl = len(dtl)
        st.write("详情数据量: " + str(lendtl))

        if lendtl > 0:
            # get min and max date
            mindate = dtl["date"].min()
            maxdate = dtl["date"].max()
            st.write("详情日期: " + maxdate + " - " + mindate)
            # detailname
            detailname = "safedtl" + org_name_index + get_now() + ".csv"
            # download detail data
            st.download_button(
                "下载详情数据",
                data=dtl.to_csv().encode("utf_8_sig"),
                file_name=detailname,
            )

        sumlist.append(oldsum)
        dtllist.append(dtl)

    # download all data
    st.markdown("##### 全部数据")

    # get all sum
    allsum = pd.concat(sumlist)
    # get all detail
    alldtl = pd.concat(dtllist)

    lensum = len(allsum)
    st.write("列表数据量: " + str(lensum))
    # get unique link number
    linkno = allsum["link"].nunique()
    st.write("链接数: " + str(linkno))
    # get min and max date
    mindate = allsum["date"].min()
    maxdate = allsum["date"].max()
    st.write("列表日期: " + maxdate + " - " + mindate)

    lendtl = len(alldtl)
    st.write("详情数据量: " + str(lendtl))
    # get unique link number
    linkno = alldtl["link"].nunique()
    st.write("链接数: " + str(linkno))
    # get min and max date
    mindate = alldtl["date"].min()
    maxdate = alldtl["date"].max()
    st.write("详情日期: " + maxdate + " - " + mindate)

    # listname
    listname = "safesumall" + get_now() + ".csv"
    # download list data
    st.download_button(
        "下载列表数据", data=allsum.to_csv().encode("utf_8_sig"), file_name=listname
    )
    # detailname
    detailname = "safedtlall" + get_now() + ".csv"
    # download detail data
    st.download_button(
        "下载详情数据", data=alldtl.to_csv().encode("utf_8_sig"), file_name=detailname
    )


# display bar chart in plotly
def display_search_df(searchdf):
    df_month = searchdf.copy()
    # df_month["发文日期"] = pd.to_datetime(df_month["发布日期"]).dt.date
    # count by month
    df_month["month"] = df_month["发布日期"].apply(lambda x: x.strftime("%Y-%m"))
    df_month_count = df_month.groupby(["month"]).size().reset_index(name="count")
    # count by month
    # fig = go.Figure(
    #     data=[go.Bar(x=df_month_count['month'], y=df_month_count['count'])])
    # fig.update_layout(title='处罚数量统计', xaxis_title='月份', yaxis_title='处罚数量')
    # st.plotly_chart(fig)

    # display checkbox to show/hide graph1
    # showgraph1 = st.sidebar.checkbox("按发文时间统计", key="showgraph1")
    # fix value of showgraph1
    showgraph1 = True
    if showgraph1:
        x_data = df_month_count["month"].tolist()
        y_data = df_month_count["count"].tolist()
        # draw echarts bar chart
        # bar = (
        #     Bar()
        #     .add_xaxis(xaxis_data=x_data)
        #     .add_yaxis(series_name="数量", y_axis=y_data, yaxis_index=0)
        #     .set_global_opts(
        #         title_opts=opts.TitleOpts(title="按发文时间统计"),
        #         visualmap_opts=opts.VisualMapOpts(max_=max(y_data), min_=min(y_data)),
        #     )
        # )
        # use events
        # events = {
        #     "click": "function(params) { console.log(params.name); return params.name }",
        #     # "dblclick":"function(params) { return [params.type, params.name, params.value] }"
        # }
        # use events
        # yearmonth = st_pyecharts(bar, events=events)
        bar, yearmonth = print_bar(x_data, y_data, "处罚数量", "按发文时间统计")
        # st.write(yearmonth)
        if yearmonth is not None:
            # get year and month value from format "%Y-%m"
            # year = int(yearmonth.split("-")[0])
            # month = int(yearmonth.split("-")[1])
            # filter date by year and month
            searchdfnew = df_month[df_month["month"] == yearmonth]
            # drop column "month"
            searchdfnew.drop(columns=["month"], inplace=True)

            # set session state
            st.session_state["search_result_safe"] = searchdfnew
            # refresh page
            # st.experimental_rerun()

        # 图一解析开始
        maxmonth = df_month["month"].max()
        minmonth = df_month["month"].min()
        # get total number of count
        num_total = len(df_month["month"])
        # get total number of month count
        month_total = len(set(df_month["month"].tolist()))
        # get average number of count per month count
        num_avg = num_total / month_total
        # get month value of max count
        top1month = max(
            set(df_month["month"].tolist()), key=df_month["month"].tolist().count
        )
        top1number = df_month["month"].tolist().count(top1month)

        image1_text = (
            "图一解析：从"
            + minmonth
            + "至"
            + maxmonth
            + "，共发生"
            + str(num_total)
            + "起处罚事件，"
            + "平均每月发生"
            + str(round(num_avg))
            + "起处罚事件。其中"
            + top1month
            + "最高发生"
            + str(top1number)
            + "起处罚事件。"
        )

        # display total coun
        st.markdown("##### " + image1_text)

    # get eventdf sum amount by month
    df_sum, df_sigle_penalty = sum_amount_by_month(df_month)

    sum_data = df_sum["sum"].tolist()
    line, yearmonthline = print_line(x_data, sum_data, "处罚金额", "案例金额统计")

    if yearmonthline is not None:
        # filter date by year and month
        searchdfnew = df_month[df_month["month"] == yearmonthline]
        # drop column "month"
        searchdfnew.drop(columns=["month"], inplace=True)
        # set session state
        st.session_state["search_result_safe"] = searchdfnew
        # refresh page
        # st.experimental_rerun()

    # 图二解析：
    sum_data_number = 0  # 把案件金额的数组进行求和
    more_than_100 = 0  # 把案件金额大于100的数量进行统计
    case_total = 0  # 把案件的总数量进行统计

    penaltycount = df_sigle_penalty["amount"].tolist()
    for i in penaltycount:
        sum_data_number = sum_data_number + i
        if i > 100:
            more_than_100 = more_than_100 + 1
        if i != 0:
            case_total = case_total + 1

    # for i in sum_data:
    #     sum_data_number = sum_data_number + i / 10000
    #     if i > 100 * 10000:
    #         more_than_100 = more_than_100 + 1
    # sum_data_number=round(sum_data_number,2)
    if case_total > 0:
        avg_sum = round(sum_data_number / case_total, 2)
    else:
        avg_sum = 0
    # get index of max sum
    topsum1 = df_sum["sum"].nlargest(1)
    topsum1_index = df_sum["sum"].idxmax()
    # get month value of max count
    topsum1month = df_sum.loc[topsum1_index, "month"]
    image2_text = (
        "图二解析：从"
        + minmonth
        + "至"
        + maxmonth
        + "，共发生罚款案件"
        + str(case_total)
        + "起;期间共涉及处罚金额"
        + str(round(sum_data_number, 2))
        + "万元，处罚事件平均处罚金额为"
        + str(avg_sum)
        + "万元，其中处罚金额高于100万元处罚事件共"
        + str(more_than_100)
        + "起。"
        + topsum1month
        + "发生最高处罚金额"
        + str(round(topsum1.values[0], 2))
        + "万元。"
    )
    st.markdown("##### " + image2_text)

    # count by orgname
    df_org_count = df_month.groupby(["区域"]).size().reset_index(name="count")
    # sort by count desc
    df_org_count = df_org_count.sort_values(by=["count"], ascending=False)
    # st.write(df_org_count)
    org_ls = df_org_count["区域"].tolist()
    count_ls = df_org_count["count"].tolist()
    new_orgls, new_countls = count_by_province(org_ls, count_ls)
    # st.write(new_orgls+ new_countls)
    map_data = print_map(new_orgls, new_countls, "处罚地图")
    # st_pyecharts(map_data, map=map, width=800, height=650)
    # display map
    # components.html(map.render_embed(), height=650)

    pie, orgname = print_pie(
        df_org_count["区域"].tolist(), df_org_count["count"].tolist(), "按发文机构统计"
    )
    if orgname is not None:
        # filter searchdf by orgname
        searchdfnew = searchdf[searchdf["区域"] == orgname]
        # set session state
        st.session_state["search_result_safe"] = searchdfnew
        # refresh page
        # st.experimental_rerun()

    # 图四解析开始
    # orgls = df_month["区域"].value_counts().keys().tolist()
    # countls = df_month["区域"].value_counts().tolist()
    result = ""

    for org, count in zip(org_ls[:3], count_ls[:3]):
        result = result + org + "（" + str(count) + "起）,"

    image4_text = (
        "图四解析："
        + minmonth
        + "至"
        + maxmonth
        + "，共"
        + str(len(org_ls))
        + "家地区监管机构提出处罚意见，"
        + "排名前三的机构为："
        + result[: len(result) - 1]
    )
    st.markdown("#####  " + image4_text)


def print_bar(x_data, y_data, y_axis_name, title):
    # Create a DataFrame from the input data
    data = pd.DataFrame({"月份": x_data, y_axis_name: y_data})
    # Create the bar chart
    fig = px.bar(
        data,
        x="月份",
        y=y_axis_name,
        title=title,
        color=y_axis_name,
        text=y_axis_name,
        color_continuous_scale=px.colors.sequential.Viridis,
    )

    # Display the chart
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    monthselected = event["selection"]["point_indices"]

    if monthselected == []:
        clickevent = None
    else:
        clickevent = x_data[monthselected[0]]

    return fig, clickevent


def print_line(x_data, y_data, y_axis_name, title):
    # Create a DataFrame from the input data
    data = pd.DataFrame({"月份": x_data, y_axis_name: y_data})
    # Create the line chart
    fig = px.line(data, x="月份", y=y_axis_name, title=title, text=y_axis_name)

    # Display the chart
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    monthselected = event["selection"]["point_indices"]

    if monthselected == []:
        clickevent = None
    else:
        clickevent = x_data[monthselected[0]]

    return fig, clickevent


def print_pie(namels, valuels, title):
    data = pd.DataFrame({"names": namels, "values": valuels})

    fig = px.pie(
        data,
        names="names",
        values="values",
        title=title,
        labels={"names": "名称", "values": "数量"},
    )
    fig.update_traces(textinfo="label+percent", insidetextorientation="radial")
    # Display the chart
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    monthselected = event["selection"]["point_indices"]

    if monthselected == []:
        clickevent = None
    else:
        clickevent = namels[monthselected[0]]

    return fig, clickevent


def print_map(province_name, province_values, title_name):
    # load the GeoJSON file
    china_geojson = json.load(open(mappath, "r", encoding="utf-8-sig"))

    # st.write(china_geojson)

    # Create a DataFrame from the provided data
    data = pd.DataFrame({"省份": province_name, "处罚数量": province_values})
    # Create the choropleth map
    # fig = px.choropleth(
    fig = px.choropleth_mapbox(
        data,
        geojson=china_geojson,
        featureidkey="properties.name",
        locations="省份",
        color="处罚数量",
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=2,
        center={"lat": 35, "lon": 105},
        # scope='asia',
        title=title_name,
    )

    # Add text labels
    fig.update_traces(
        text=data["处罚数量"],
    )

    # Update geos
    fig.update_geos(
        visible=False,
        fitbounds="locations",
    )

    # Update layout
    fig.update_layout(title_text=title_name, title_x=0.5)

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    return fig


def count_by_province(city_ls, count_ls):
    if len(city_ls) != len(count_ls):
        raise ValueError("城市列表和计数列表的长度必须相同")

    # Use Counter for efficient counting
    province_counts = Counter()

    # Use list comprehension for faster iteration
    province_counts.update(
        {city2province[loc]: count for loc, count in zip(city_ls, count_ls)}
    )

    # Use sorted with key function for efficient sorting
    sorted_provinces = sorted(province_counts.items(), key=lambda x: (-x[1], x[0]))

    # Use zip for efficient unpacking
    provinces, counts = zip(*sorted_provinces)

    return list(provinces), list(counts)


def update_safelabel():
    # get safe detail
    safedf = get_safedetail("")
    # drop null value
    safedf = safedf.dropna(subset=["违法事实"])
    st.text(safedf.columns)

    touptdf = safedf[
        ["link", "罚款金额（万元）", "没收金额（万元）", "罚没款金额（万元）"]
    ]
    # fillna with 0
    touptdf.fillna(0, inplace=True)
    # set amount value
    touptdf["amount"] = (
        touptdf["罚款金额（万元）"].astype(float)
        + touptdf["没收金额（万元）"].astype(float)
        + touptdf["罚没款金额（万元）"].astype(float)
    )

    amtupddf = touptdf[["link", "amount"]]
    # reset index
    amtupddf.reset_index(drop=True, inplace=True)
    # display newdf
    st.markdown("### 分类数据")
    st.write(amtupddf)
    # if newdf is not empty, save it
    if amtupddf.empty is False:
        updlen = len(amtupddf)
        st.info("待更新分类" + str(updlen) + "条数据")
        savename = "safe_tocat" + get_now() + ".csv"
        # download detail data
        st.download_button(
            "下载分类案例数据",
            data=amtupddf.to_csv().encode("utf_8_sig"),
            file_name=savename,
        )
    else:
        st.info("无待更新分类数据")


def get_safecat():
    amtdf = get_csvdf(pensafe, "safecat")
    # process amount
    amtdf["amount"] = amtdf["amount"].astype(float)
    # return amtdf[["id", "amount"]]
    return amtdf


def sum_amount_by_month(df):
    df1 = df
    df1["amount"] = df1["amount"].fillna(0)
    df1["发布日期"] = pd.to_datetime(df1["发布日期"]).dt.date
    # df=df[df['发文日期']>=pd.to_datetime('2020-01-01')]
    df1["month"] = df1["发布日期"].apply(lambda x: x.strftime("%Y-%m"))
    df_month_sum = df1.groupby(["month"])["amount"].sum().reset_index(name="sum")
    df_sigle_penalty = df1[["month", "amount"]]
    return df_month_sum, df_sigle_penalty
