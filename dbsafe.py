"""
Database safety information processing and display module.

This module provides functions for displaying and managing safety enforcement data
from regulatory authorities.
"""
import csv
import os
from typing import Dict, List, Tuple, Optional, Union

import pandas as pd
import streamlit as st

from data_processing import get_safedetail
from utils import get_csvdf, parse_date, savedf, get_now
from visualization import display_search_df


# Constants
pensafe = "safe"
mappath = "map/chinageo.json"
temppath = "temp"

# Mapping of Chinese organization names to their English equivalents
org2name: Dict[str, str] = {
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

# Mapping of cities to their respective provinces
city2province: Dict[str, str] = {
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

# URL constants
baseurl = "http://www.safe.gov.cn/www/illegal/index?page="
org2url: Dict[str, str] = {
    "北京": "http://beijing.pbc.gov.cn/beijing/113682/113700/113707/10983/index",
}


def display_eventdetail(search_df: pd.DataFrame) -> None:
    """
    Display event details for the provided search DataFrame.
    
    Args:
        search_df: DataFrame containing search results
    """
    display_search_df(search_df)
    
    search_dfnew = st.session_state["search_result_safe"]
    total = len(search_dfnew)
    
    st.markdown(f"### 搜索结果({total}条)")
    
    st.download_button(
        "下载搜索结果",
        data=search_dfnew.to_csv().encode("utf_8_sig"),
        file_name="搜索结果.csv",
    )
    
    # Define columns for display
    discols = [
        "发布日期",
        "行政处罚决定书文号",
        "违规主体名称",
        "违法事实",
        "区域",
        "link",
    ]
    
    display_df = search_dfnew[discols]
    data = st.dataframe(display_df, on_select="rerun", selection_mode="single-row")
    selected_rows = data["selection"]["rows"]
    
    if selected_rows == []:
        st.error("请先选择查看案例")
        st.stop()

    id = display_df.loc[selected_rows[0], "link"]
    st.markdown("##### 案情经过")
    
    # Filter and prepare detailed data for display
    selected_rows_df = search_dfnew[search_dfnew["link"] == id]
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
    
    # Rename columns for display
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

    # Transpose and display as table
    selected_rows_df = selected_rows_df.astype(str).T
    selected_rows_df.columns = ["内容"]
    
    st.table(selected_rows_df)
    
    # Display case link
    url = selected_rows_df.loc["链接", "内容"]
    st.markdown("##### 案例链接")
    st.markdown(url)


def display_summary() -> pd.DataFrame:
    """
    Display summary of case data.
    
    Returns:
        DataFrame containing summary information by region
    """
    oldsum2 = get_safedetail("")
    oldlen2 = len(oldsum2)
    
    min_date2 = oldsum2["发布日期"].min()
    max_date2 = oldsum2["发布日期"].max()
    
    # Display metrics in columns
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("案例总数", oldlen2)
    with col2:
        st.metric("案例日期范围", f"{min_date2} - {max_date2}")

    # Create and display summary by region
    sumdf2 = (
        oldsum2.groupby("区域")["发布日期"].agg(["max", "min", "count"]).reset_index()
    )
    sumdf2.columns = ["区域", "最近发文日期", "最早发文日期", "案例总数"]
    sumdf2.sort_values(by=["最近发文日期"], ascending=False, inplace=True)
    sumdf2.reset_index(drop=True, inplace=True)
    
    st.markdown("#### 按区域统计")
    st.table(sumdf2)

    return sumdf2


def display_safesum(org_name_ls: List[str]) -> None:
    """
    Display summary for each organization in the list.
    
    Args:
        org_name_ls: List of organization names to display summaries for
    """
    for org_name in org_name_ls:
        st.markdown(f"#### {org_name}")
        
        # Display list summary
        st.markdown("列表")
        oldsum = get_safesum(org_name)
        display_suminfo(oldsum)
        
        # Display detail summary
        st.markdown("详情")
        dtl = get_safedetail(org_name)
        dtl = dtl.dropna(subset=["违法事实"])
        display_suminfo(dtl)


def get_safesum(orgname: str) -> pd.DataFrame:
    """
    Get summary data for the specified organization.
    
    Args:
        orgname: Organization name to filter by
        
    Returns:
        DataFrame containing summary data for the organization
    """
    beginwith = "safesum"
    allpendf = get_csvdf(pensafe, beginwith)
    pendf = allpendf[allpendf["区域"] == orgname]
    
    if len(pendf) > 0:
        pendf = pendf.copy()
        pendf.loc[:, "发布日期"] = pendf["date"].apply(parse_date)
    
    return pendf


def display_suminfo(df: pd.DataFrame) -> None:
    """
    Display summary information for the provided DataFrame.
    
    Args:
        df: DataFrame containing data to summarize
    """
    oldlen = len(df)
    if oldlen > 0:
        linkno = df["link"].nunique()
        min_date = df["发布日期"].min()
        max_date = df["发布日期"].max()
        
        # Display metrics in columns
        col1, col2, col3 = st.columns([1, 1, 1])
        col1.write(f"案例总数：{oldlen}")
        col2.write(f"链接数：{linkno}")
        col3.write(f"日期范围：{min_date} - {max_date}")


def savetempsub(df: pd.DataFrame, basename: str, subfolder: str) -> None:
    """
    Save DataFrame to a sub folder under the temp folder.
    
    Args:
        df: DataFrame to save
        basename: Base filename (without .csv extension)
        subfolder: Name of subfolder under temp directory
    """
    savename = basename + ".csv"
    savepath = os.path.join(temppath, subfolder, savename)
    
    # Create directory if it doesn't exist
    if not os.path.exists(os.path.join(temppath, subfolder)):
        os.makedirs(os.path.join(temppath, subfolder))
    
    # Save with appropriate CSV options
    df.to_csv(savepath, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\")


def update_safelabel() -> None:
    """Update case labels with financial amount information."""
    safedf = get_safedetail("")
    safedf = safedf.dropna(subset=["违法事实"])
    st.text(safedf.columns)

    # Extract financial columns
    touptdf = safedf[
        ["link", "罚款金额（万元）", "没收金额（万元）", "罚没款金额（万元）"]
    ]
    
    # Fill NaN values and convert to float
    touptdf = touptdf.fillna(0)
    for col in ["罚款金额（万元）", "没收金额（万元）", "罚没款金额（万元）"]:
        touptdf[col] = touptdf[col].astype(float)
    
    # Calculate total amount
    touptdf["amount"] = (
        touptdf["罚款金额（万元）"] + 
        touptdf["没收金额（万元）"] + 
        touptdf["罚没款金额（万元）"]
    )

    # Prepare output dataset
    amount_df = touptdf[["link", "amount"]].reset_index(drop=True)
    
    # Display results
    st.markdown("### 分类数据")
    st.write(amount_df)
    
    # Provide download option if data exists
    if not amount_df.empty:
        record_count = len(amount_df)
        st.info(f"待更新分类{record_count}条数据")
        filename = f"safe_tocat{get_now()}.csv"
        
        st.download_button(
            "下载分类案例数据",
            data=amount_df.to_csv().encode("utf_8_sig"),
            file_name=filename,
        )
    else:
        st.info("无待更新分类数据")


def get_safecat() -> pd.DataFrame:
    """
    Get case category data.
    
    Returns:
        DataFrame containing case categories with amount information
    """
    amtdf = get_csvdf(pensafe, "safecat")
    amtdf["amount"] = amtdf["amount"].astype(float)
    return amtdf


def sum_amount_by_month(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate monthly financial amount summaries.
    
    Args:
        df: DataFrame containing case data with date and amount information
        
    Returns:
        Tuple of (monthly sum DataFrame, single penalty DataFrame)
    """
    df1 = df.copy()
    df1["amount"] = df1["amount"].fillna(0)
    df1["发布日期"] = pd.to_datetime(df1["发布日期"]).dt.date
    df1["month"] = df1["发布日期"].apply(lambda x: x.strftime("%Y-%m"))
    
    # Calculate monthly sums
    df_month_sum = df1.groupby(["month"])["amount"].sum().reset_index(name="sum")
    df_single_penalty = df1[["month", "amount"]]
    
    return df_month_sum, df_single_penalty
