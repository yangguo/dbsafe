import time
import random
import pandas as pd
import streamlit as st
from selenium.webdriver.common.by import By

from snapshot import get_chrome_driver, get_safari_driver
from utils import get_csvdf, get_now, savedf
from data_processing import get_safedetail


# Constants
baseurl = "http://www.safe.gov.cn/www/illegal/index?page="
pensafe = "safe"
temppath = "temp"


# Import after constant definitions to avoid circular imports
from dbsafe import org2name, savetempsub, get_safesum


def get_sumeventdf(orgname, start, end):
    """
    Scrape event summary data for a given organization across a range of pages.
    
    Args:
        orgname: Name of the organization to scrape
        start: Starting page number
        end: Ending page number
        
    Returns:
        DataFrame containing scraped event summaries
    """
    org_name_index = org2name[orgname]
    browser = get_chrome_driver(temppath)
    cityname = org_name_index

    resultls = []
    errorls = []
    count = 0
    
    for n in range(start, end + 1):
        st.info(f"page: {n}")
        st.info(f"{count} begin")
        url = baseurl + str(n) + "&siteid=" + cityname
        st.info(f"url: {url}")
        
        try:
            browser.implicitly_wait(3)
            browser.get(url)
            
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
            st.info(f"finished: {n}")
            
        except Exception as e:
            st.error(f"error!: {e}")
            errorls.append(url)

        mod = (n + 1) % 2
        if mod == 0 and count > 0:
            tempdf = pd.concat(resultls)
            savename = f"tempsum-{org_name_index}{count + 1}"
            savedf(tempdf, savename)

        wait = random.randint(2, 20)
        time.sleep(wait)
        st.info(f"finish: {count}")
        count += 1

    browser.quit()
    
    if len(resultls) > 0:
        sumdf = pd.concat(resultls)
        sumdf["区域"] = orgname
        savedf(sumdf, f"tempsumall-{org_name_index}{count}")
    else:
        sumdf = pd.DataFrame()

    return sumdf


def update_sumeventdf(currentsum, orgname):
    """
    Update event summary data with new records.
    
    Args:
        currentsum: DataFrame with current event summaries
        orgname: Name of the organization
        
    Returns:
        DataFrame containing new event summaries
    """
    org_name_index = org2name[orgname]
    oldsum = get_safesum(orgname)
    
    if oldsum.empty:
        oldidls = []
    else:
        oldidls = oldsum["link"].tolist()
        
    currentidls = currentsum["link"].tolist()
    newidls = [x for x in currentidls if x not in oldidls]
    newdf = currentsum[currentsum["link"].isin(newidls)]
    
    if not newdf.empty:
        newdf.reset_index(drop=True, inplace=True)
        nowstr = get_now()
        savename = f"safesum{org_name_index}{nowstr}"
        newdf["区域"] = orgname
        savedf(newdf, savename)
        
    return newdf


def toupt_safesum(org_name_ls):
    """
    Identify organizations that need updates by comparing summary and detail counts.
    
    Args:
        org_name_ls: List of organization names to check
        
    Returns:
        List of organizations that need updates
    """
    touptls = []
    
    for org_name in org_name_ls:
        oldsum = get_safesum(org_name)
        lensum = len(oldsum)
        
        dtl = get_safedetail(org_name)
        dtl = dtl.dropna(subset=["违法事实"])
        lendtl = len(dtl)
        
        if lensum > lendtl:
            touptls.append(org_name)
            
    return touptls


def update_toupd(orgname):
    """
    Identify records that need detail updates.
    
    Args:
        orgname: Name of the organization
        
    Returns:
        DataFrame containing records that need updates
    """
    org_name_index = org2name[orgname]
    currentsum = get_safesum(orgname)
    
    oldsum = get_safedetail(orgname)
    oldsum = oldsum.dropna(subset=["违法事实"])
    
    if oldsum.empty:
        oldidls = []
    else:
        oldidls = [] if "link" not in oldsum.columns else oldsum["link"].tolist()
        
    if currentsum.empty:
        currentidls = []
    else:
        currentidls = currentsum["link"].tolist()
        
    newidls = [x for x in currentidls if x not in oldidls]

    if currentsum.empty:
        newdf = pd.DataFrame()
    else:
        newdf = currentsum[currentsum["link"].isin(newidls)]
        
    if not newdf.empty:
        newdf.sort_values(by=["date"], ascending=False, inplace=True)
        newdf.reset_index(drop=True, inplace=True)
        
        toupdname = f"safetoupd{org_name_index}"
        newdf.loc[:, "区域"] = orgname
        savedf(newdf, toupdname)
        
    return newdf


def get_safetoupd(orgname):
    """
    Get records that need detail updates for a specific organization.
    
    Args:
        orgname: Name of the organization
        
    Returns:
        DataFrame containing records that need updates
    """
    org_name_index = org2name[orgname]
    beginwith = f"safetoupd{org_name_index}"
    pendf = get_csvdf(pensafe, beginwith)
    return pendf


def get_eventdetail(eventsum, orgname):
    """
    Scrape detailed event information for a list of events.
    
    Args:
        eventsum: DataFrame containing event summaries
        orgname: Name of the organization
        
    Returns:
        DataFrame containing detailed event information
    """
    org_name_index = org2name[orgname]
    browser = get_safari_driver()
    detaills = eventsum["link"].tolist()
    datels = eventsum["date"].tolist()

    resultls = []
    errorls = []
    count = 0
    
    for date, durl in zip(datels, detaills):
        st.info(f"{count} begin")
        st.info(f"url: {durl}")
        
        try:
            browser.get(durl)
            hl1 = browser.find_elements(By.XPATH, "//body//th")
            dl1 = browser.find_elements(By.XPATH, "//body//td")
            
            df = web2table(hl1, dl1)
            df["link"] = durl
            df["date"] = date
            resultls.append(df)

        except Exception as e:
            st.error(f"error!: {e}")
            st.error(f"check url: {durl}")
            errorls.append(durl)

        mod = (count + 1) % 10
        if mod == 0 and count > 0:
            if resultls:
                tempdf = pd.concat(resultls)
                tempdf["区域"] = orgname
                savename = f"tempdtl-{org_name_index}{count + 1}"
                savetempsub(tempdf, savename, org_name_index)

        wait = random.randint(2, 20)
        time.sleep(wait)
        st.info(f"finish: {count}")
        count += 1

    browser.quit()
    
    if len(errorls) > 0:
        st.error("error list:")
        st.error(errorls)
        
    if resultls:
        safedf = pd.concat(resultls)
        safedf["区域"] = orgname
        savecsv = f"safedtl{org_name_index}{get_now()}"
        safedf.reset_index(drop=True, inplace=True)
        
        savetempsub(safedf, savecsv, org_name_index)
        savedf(safedf, savecsv)
    else:
        safedf = pd.DataFrame()

    return safedf


def web2table(headers, data):
    """
    Convert web table headers and data into a DataFrame.
    
    Args:
        headers: List of header elements
        data: List of data elements
        
    Returns:
        DataFrame containing table data
    """
    headls = [h.text for h in headers]
    contls = [d.text for d in data]
    row_data = dict(zip(headls, contls))
    df = pd.DataFrame(row_data, index=[0])
    return df


def download_safesum():
    """
    Create download options for safety summary data by organization and in aggregate.
    """
    st.markdown("#### 案例数据下载")
    st.markdown("##### 按区域下载")

    sumlist = []
    dtllist = []

    for orgname in org2name.keys():
        st.markdown(f"##### {orgname}")
        org_name_index = org2name[orgname]
        
        # Get and display summary data
        oldsum = get_safesum(orgname)
        lensum = len(oldsum)
        st.write(f"列表数据量: {lensum}")

        if lensum > 0:
            mindate = oldsum["date"].min()
            maxdate = oldsum["date"].max()
            st.write(f"列表日期: {maxdate} - {mindate}")
            
            listname = f"safesum{org_name_index}{get_now()}.csv"
            st.download_button(
                "下载列表数据",
                data=oldsum.to_csv().encode("utf_8_sig"),
                file_name=listname,
            )
        
        # Get and display detail data
        dtl = get_safedetail(orgname)
        dtl = dtl.dropna(subset=["违法事实"])
        lendtl = len(dtl)
        st.write(f"详情数据量: {lendtl}")

        if lendtl > 0:
            mindate = dtl["date"].min()
            maxdate = dtl["date"].max()
            st.write(f"详情日期: {maxdate} - {mindate}")
            
            detailname = f"safedtl{org_name_index}{get_now()}.csv"
            st.download_button(
                "下载详情数据",
                data=dtl.to_csv().encode("utf_8_sig"),
                file_name=detailname,
            )

        sumlist.append(oldsum)
        dtllist.append(dtl)

    # Provide download options for aggregate data
    st.markdown("##### 全部数据")

    allsum = pd.concat(sumlist)
    alldtl = pd.concat(dtllist)

    # Display summary statistics
    lensum = len(allsum)
    st.write(f"列表数据量: {lensum}")
    
    linkno = allsum["link"].nunique()
    st.write(f"链接数: {linkno}")
    
    mindate = allsum["date"].min()
    maxdate = allsum["date"].max()
    st.write(f"列表日期: {maxdate} - {mindate}")

    lendtl = len(alldtl)
    st.write(f"详情数据量: {lendtl}")
    
    linkno = alldtl["link"].nunique()
    st.write(f"链接数: {linkno}")
    
    mindate = alldtl["date"].min()
    maxdate = alldtl["date"].max()
    st.write(f"详情日期: {maxdate} - {mindate}")

    # Provide download buttons
    listname = f"safesumall{get_now()}.csv"
    st.download_button(
        "下载列表数据", 
        data=allsum.to_csv().encode("utf_8_sig"), 
        file_name=listname
    )
    
    detailname = f"safedtlall{get_now()}.csv"
    st.download_button(
        "下载详情数据", 
        data=alldtl.to_csv().encode("utf_8_sig"), 
        file_name=detailname
    )
