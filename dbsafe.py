import glob

import pandas as pd
import streamlit as st
import time
from snapshot import get_chrome_driver
from selenium.webdriver.common.by import By
import random
import os
import datetime
import csv

pensafe = "safe"
mapfolder = "map"
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
    ]  # [col]
    # sort by date desc
    searchdf.sort_values(by=["发布日期"], ascending=False, inplace=True)
    # drop duplicates
    # searchdf.drop_duplicates(subset=["link"], inplace=True)
    # reset index
    searchdf.reset_index(drop=True, inplace=True)
    return searchdf


def display_eventdetail(search_df):
    # draw plotly figure
    # display_cbircmonth(search_df)
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
    discols = ["发布日期", "行政处罚决定书文号", "违规主体名称", "违法事实", "区域"]
    # get display df
    display_df = search_dfnew[discols]
    # set index column using loc
    # display_df["序号"] = display_df.index
    display_df.loc[:, "序号"] = display_df.index
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
    id = display_df.loc[selected_rows[0], "序号"]
    # display event detail
    st.markdown("##### 案情经过")
    # select search_dfnew by id
    selected_rows_df = search_dfnew[search_dfnew.index == id]
    # transpose and set column name
    selected_rows_df = selected_rows_df.astype(str).T

    selected_rows_df.columns = ["内容"]
    # display selected rows
    st.table(selected_rows_df)

    # get event detail url
    url = selected_rows_df.loc["link", "内容"]
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
        st.write(org_name)
        oldsum = get_safesum(org_name)
        maxsumdate = oldsum["发布日期"].max()
        dtl = get_safedetail(org_name)
        maxdtldate = dtl["发布日期"].max()
        if maxdtldate < maxsumdate:
            touptls.append(org_name)
    return touptls


# update toupd
def update_toupd(orgname):
    org_name_index = org2name[orgname]
    # get sumeventdf
    currentsum = get_safesum(orgname)
    # get detail
    oldsum = get_safedetail(orgname)
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
        newdf["区域"] = orgname
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
    browser = get_chrome_driver(temppath)
    # browser = get_safari_driver()
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
    # get min and max date
    mindate = allsum["date"].min()
    maxdate = allsum["date"].max()
    st.write("列表日期: " + maxdate + " - " + mindate)

    lendtl = len(alldtl)
    st.write("详情数据量: " + str(lendtl))
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
