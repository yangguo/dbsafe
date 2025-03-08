"""
DBSafe - 外管局监管处罚分析 (Regulatory Enforcement Analysis)

A Streamlit application for scraping, analyzing, and visualizing regulatory enforcement cases 
from Chinese financial regulatory authorities.

This module serves as the main entry point for the Streamlit application, providing
the user interface and coordinating the various components of the system.

Copyright (c) 2023-2024
License: Apache License 2.0 (see LICENSE file for details)
"""
import pandas as pd
import streamlit as st

from dbsafe import (
    get_safedetail,
    searchsafe,
    display_eventdetail,
    display_summary,
    display_safesum,
    get_sumeventdf,
    update_sumeventdf,
    toupt_safesum,
    update_toupd,
    get_safetoupd,
    get_eventdetail,
    download_safesum,
    update_safelabel,
    get_safecat,
)


# Constants
TEMP_PATH = "temp"

# City list
CITY_LIST = [
    "北京", "厦门", "青海", "甘肃", "天津", "河北", "贵州", "湖南", "深圳", "江西",
    "广东", "重庆", "黑龙江", "福建", "河南", "陕西", "海南", "云南", "湖北", "山东",
    "新疆", "宁波", "大连", "江苏", "内蒙古", "浙江", "吉林", "广西", "上海", "宁夏",
    "安徽", "山西", "青岛", "辽宁", "西藏", "四川", "总部",
]


# Set page config
st.set_page_config(
    page_title="外管局监管处罚分析",
    page_icon=":bank:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def update_case_list(org_name_ls, start_num, end_num):
    """
    Update case lists for the selected organizations.
    
    Scrapes case list data from regulatory websites for each organization
    within the specified page range and updates the local database.
    
    Args:
        org_name_ls: List of organization names to update
        start_num: Starting page number for scraping
        end_num: Ending page number for scraping
    """
    for org_name in org_name_ls:
        st.markdown(f"#### 更新列表：{org_name}")
        start = start_num
        end = end_num

        while True:
            # Get and update event data
            sumeventdf = get_sumeventdf(org_name, start, end)
            length = len(sumeventdf)
            st.success(f"获取了{length}条案例")
            
            newsum = update_sumeventdf(sumeventdf, org_name)
            sumevent_len = len(newsum)
            st.success(f"共{sumevent_len}条案例待更新")

            # If all records need updating and we have records, continue to next page
            if sumevent_len == length and length > 0:
                start = end + 1
                end = end + 1
            else:
                break


def update_case_details(org_name_ls):
    """
    Update case details for the selected organizations.
    
    Retrieves detailed case information from regulatory websites for each organization
    that has pending updates and saves them to the local database.
    
    Args:
        org_name_ls: List of organization names to update
    """
    for org_name in org_name_ls:
        st.markdown(f"#### 更新详情：{org_name}")
        
        newsum = update_toupd(org_name)
        newsum_len = len(newsum)
        st.success(f"共{newsum_len}条案例待更新")
        
        if newsum_len > 0:
            toupd = get_safetoupd(org_name)
            st.write(toupd)
            
            eventdetail = get_eventdetail(toupd, org_name)
            eventdetail_len = len(eventdetail)
            st.success(f"更新完成，共{eventdetail_len}条案例详情")
        else:
            st.error("没有更新的案例")


def handle_case_search():
    """
    Handle the case search functionality.
    
    Manages the search form UI, performs search operations based on user inputs,
    and displays results through data visualization. Includes options for date ranges,
    keyword searches, regional filters, and minimum penalty thresholds.
    """
    # Initialize session state if needed
    if "search_result_safe" not in st.session_state:
        st.session_state["search_result_safe"] = None
    if "keywords_safe" not in st.session_state:
        st.session_state["keywords_safe"] = []

    # Get and prepare data
    dfl = get_safedetail("")
    dfl = dfl.dropna(subset=["违法事实"])
    dfl = dfl.fillna("")
    
    catdf = get_safecat()
    dfl = pd.merge(dfl, catdf, on="link", how="left")
    
    # Get date ranges
    min_date = dfl["发布日期"].min()
    max_date = dfl["发布日期"].max()
    one_year_ago = max_date - pd.Timedelta(days=365)
    
    loclist = CITY_LIST

    # Create search form
    with st.form("搜索案例"):
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("开始日期", value=one_year_ago, min_value=min_date)
            wenhao_text = st.text_input("文号关键词")
            people_text = st.text_input("当事人关键词")
            event_text = st.text_input("案情关键词")
            min_penalty = st.number_input("最低处罚金额(万元)", value=0)
            
        with col2:
            end_date = st.date_input("结束日期", value=max_date, min_value=min_date)
            penalty_text = st.text_input("处罚决定关键词")
            org_text = st.text_input("处罚机关关键词")
            province = st.multiselect("处罚区域", loclist)
            
        searchbutton = st.form_submit_button("搜索")
    
    # Process search
    search_df = None
    if searchbutton:
        # Validate inputs
        if all(text == "" for text in [wenhao_text, people_text, event_text, penalty_text, org_text]):
            st.warning("请输入搜索关键词")
            
        if not province:
            province = loclist
            
        # Save search parameters
        st.session_state["keywords_safe"] = [
            start_date,
            end_date,
            wenhao_text,
            people_text,
            event_text,
            penalty_text,
            org_text,
            province,
            min_penalty,
        ]
        
        # Perform search
        search_df = searchsafe(
            dfl,
            start_date,
            end_date,
            wenhao_text,
            people_text,
            event_text,
            penalty_text,
            org_text,
            province,
            min_penalty,
        )
        
        st.session_state["search_result_safe"] = search_df
    else:
        search_df = st.session_state["search_result_safe"]
    
    # Display results
    if search_df is None:
        st.error("请先搜索")
        st.stop()
    elif len(search_df) > 0:
        display_eventdetail(search_df)
    else:
        st.warning("没有搜索结果")


def handle_case_update():
    """
    Handle the case update functionality.
    
    Manages organization selection and provides update options
    for case lists and case details. Includes functionality to identify
    organizations with pending updates and facilitates data refresh operations.
    """
    # Select organizations
    org_name_ls = st.sidebar.multiselect("机构", CITY_LIST)
    if not org_name_ls:
        org_name_ls = CITY_LIST

    # Save to session state
    st.session_state["org_name_ls"] = org_name_ls

    # Filter for pending organizations if checked
    pendingorg = st.sidebar.checkbox("待更新机构")
    if pendingorg:
        org_name_ls = toupt_safesum(org_name_ls)
        st.markdown("#### 待更新机构")
        orglsstr = ", ".join(org_name_ls)
        st.markdown(f"#### {orglsstr}")

    # Display summary
    display_safesum(org_name_ls)

    # Page number inputs
    start_num = int(st.sidebar.number_input("起始页", value=1, min_value=1))
    end_num = int(st.sidebar.number_input("结束页", value=1))

    # Update buttons
    if st.sidebar.button("更新列表"):
        update_case_list(org_name_ls, start_num, end_num)
        
    if st.sidebar.button("更新详情"):
        update_case_details(org_name_ls)

    # Refresh button
    if st.sidebar.button("刷新页面"):
        st.experimental_rerun()


def main():
    """
    Main function to run the Streamlit application.
    
    Sets up the navigation menu and routes to the appropriate functionality
    based on user selection. The main components include case summary display,
    case search, case update, case download, and case classification.
    """
    menu = [
        "案例总数",
        "案例搜索",
        "案例更新",
        "案例下载",
        "案例分类",
    ]

    choice = st.sidebar.selectbox("选择", menu)

    if choice == "案例总数":
        st.subheader("案例总数")
        display_summary()
        
    elif choice == "案例更新":
        st.subheader("案例更新")
        handle_case_update()
        
    elif choice == "案例搜索":
        st.subheader("案例搜索")
        handle_case_search()
        
    elif choice == "案例下载":
        download_safesum()
        
    elif choice == "案例分类":
        if st.button("生成分类案例"):
            update_safelabel()


if __name__ == "__main__":
    main()
