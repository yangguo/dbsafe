import json
import pandas as pd
import streamlit as st
import plotly.express as px
from collections import Counter

from dbsafe import city2province, sum_amount_by_month

# Define map path constant
mappath = "map/chinageo.json"


def display_search_df(searchdf):
    """
    Display visualizations for search results data.
    
    Args:
        searchdf: DataFrame containing search results
    """
    df_month = searchdf.copy()
    df_month["month"] = df_month["发布日期"].apply(lambda x: x.strftime("%Y-%m"))
    df_month_count = df_month.groupby(["month"]).size().reset_index(name="count")
    
    # Display penalty count by month chart
    x_data = df_month_count["month"].tolist()
    y_data = df_month_count["count"].tolist()
    
    bar, yearmonth = print_bar(x_data, y_data, "处罚数量", "按发文时间统计")
    
    if yearmonth is not None:
        searchdfnew = df_month[df_month["month"] == yearmonth]
        searchdfnew.drop(columns=["month"], inplace=True)
        st.session_state["search_result_safe"] = searchdfnew

    # Show analysis of bar chart data
    maxmonth = df_month["month"].max()
    minmonth = df_month["month"].min()
    num_total = len(df_month["month"])
    month_total = len(set(df_month["month"].tolist()))
    num_avg = num_total / month_total
    
    top1month = max(
        set(df_month["month"].tolist()), key=df_month["month"].tolist().count
    )
    top1number = df_month["month"].tolist().count(top1month)

    image1_text = (
        f"图一解析：从{minmonth}至{maxmonth}，共发生{num_total}起处罚事件，"
        f"平均每月发生{round(num_avg)}起处罚事件。其中{top1month}最高发生{top1number}起处罚事件。"
    )
    
    st.markdown(f"##### {image1_text}")

    # Display penalty amount by month chart
    df_sum, df_single_penalty = sum_amount_by_month(df_month)
    sum_data = df_sum["sum"].tolist()
    
    line, yearmonthline = print_line(x_data, sum_data, "处罚金额", "案例金额统计")
    
    if yearmonthline is not None:
        searchdfnew = df_month[df_month["month"] == yearmonthline]
        searchdfnew.drop(columns=["month"], inplace=True)
        st.session_state["search_result_safe"] = searchdfnew

    # Show analysis of line chart data
    sum_data_number = 0
    more_than_100 = 0
    case_total = 0

    penaltycount = df_single_penalty["amount"].tolist()
    for i in penaltycount:
        sum_data_number += i
        if i > 100:
            more_than_100 += 1
        if i != 0:
            case_total += 1

    if case_total > 0:
        avg_sum = round(sum_data_number / case_total, 2)
    else:
        avg_sum = 0
        
    topsum1 = df_sum["sum"].nlargest(1)
    topsum1_index = df_sum["sum"].idxmax()
    topsum1month = df_sum.loc[topsum1_index, "month"]
    
    image2_text = (
        f"图二解析：从{minmonth}至{maxmonth}，共发生罚款案件{case_total}起;"
        f"期间共涉及处罚金额{round(sum_data_number, 2)}万元，处罚事件平均处罚金额为{avg_sum}万元，"
        f"其中处罚金额高于100万元处罚事件共{more_than_100}起。"
        f"{topsum1month}发生最高处罚金额{round(topsum1.values[0], 2)}万元。"
    )
    
    st.markdown(f"##### {image2_text}")

    # Display penalty count by region
    df_org_count = df_month.groupby(["区域"]).size().reset_index(name="count")
    df_org_count = df_org_count.sort_values(by=["count"], ascending=False)
    
    org_ls = df_org_count["区域"].tolist()
    count_ls = df_org_count["count"].tolist()
    
    # Create region map visualization
    new_orgls, new_countls = count_by_province(org_ls, count_ls)
    map_data = print_map(new_orgls, new_countls, "处罚地图")

    # Create organization pie chart
    pie, orgname = print_pie(
        df_org_count["区域"].tolist(), 
        df_org_count["count"].tolist(), 
        "按发文机构统计"
    )
    
    if orgname is not None:
        searchdfnew = searchdf[searchdf["区域"] == orgname]
        st.session_state["search_result_safe"] = searchdfnew

    # Show analysis of pie chart data
    result = ""
    for org, count in zip(org_ls[:3], count_ls[:3]):
        result += f"{org}（{count}起）,"

    image4_text = (
        f"图四解析：{minmonth}至{maxmonth}，共{len(org_ls)}家地区监管机构提出处罚意见，"
        f"排名前三的机构为：{result[:-1]}"
    )
    
    st.markdown(f"#####  {image4_text}")


def print_bar(x_data, y_data, y_axis_name, title):
    """
    Create and display a bar chart.
    
    Args:
        x_data: List of x-axis values (usually months)
        y_data: List of y-axis values
        y_axis_name: Name of the y-axis
        title: Title of the chart
        
    Returns:
        Tuple of (figure, clicked month or None)
    """
    data = pd.DataFrame({"月份": x_data, y_axis_name: y_data})
    
    fig = px.bar(
        data,
        x="月份",
        y=y_axis_name,
        title=title,
        color=y_axis_name,
        text=y_axis_name,
        color_continuous_scale=px.colors.sequential.Viridis,
    )

    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
    monthselected = event["selection"]["point_indices"]

    clickevent = None if monthselected == [] else x_data[monthselected[0]]

    return fig, clickevent


def print_line(x_data, y_data, y_axis_name, title):
    """
    Create and display a line chart.
    
    Args:
        x_data: List of x-axis values (usually months)
        y_data: List of y-axis values
        y_axis_name: Name of the y-axis
        title: Title of the chart
        
    Returns:
        Tuple of (figure, clicked month or None)
    """
    data = pd.DataFrame({"月份": x_data, y_axis_name: y_data})
    
    fig = px.line(
        data, 
        x="月份", 
        y=y_axis_name, 
        title=title, 
        text=y_axis_name
    )

    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
    monthselected = event["selection"]["point_indices"]

    clickevent = None if monthselected == [] else x_data[monthselected[0]]

    return fig, clickevent


def print_pie(namels, valuels, title):
    """
    Create and display a pie chart.
    
    Args:
        namels: List of slice names
        valuels: List of slice values
        title: Title of the chart
        
    Returns:
        Tuple of (figure, clicked name or None)
    """
    data = pd.DataFrame({"names": namels, "values": valuels})

    fig = px.pie(
        data,
        names="names",
        values="values",
        title=title,
        labels={"names": "名称", "values": "数量"},
    )
    
    fig.update_traces(textinfo="label+percent", insidetextorientation="radial")
    
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
    monthselected = event["selection"]["point_indices"]

    clickevent = None if monthselected == [] else namels[monthselected[0]]

    return fig, clickevent


def print_map(province_name, province_values, title_name):
    """
    Create and display a choropleth map of China.
    
    Args:
        province_name: List of province names
        province_values: List of values for each province
        title_name: Title of the map
        
    Returns:
        Map figure
    """
    china_geojson = json.load(open(mappath, "r", encoding="utf-8-sig"))
    data = pd.DataFrame({"省份": province_name, "处罚数量": province_values})
    
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
        title=title_name,
    )

    # Add text labels
    fig.update_traces(text=data["处罚数量"])

    # Update geos
    fig.update_geos(
        visible=False,
        fitbounds="locations",
    )

    # Update layout
    fig.update_layout(title_text=title_name, title_x=0.5)

    st.plotly_chart(fig, use_container_width=True)
    return fig


def count_by_province(city_ls, count_ls):
    """
    Group city counts by province.
    
    Args:
        city_ls: List of cities
        count_ls: List of counts corresponding to each city
        
    Returns:
        Tuple of (province list, count list)
    """
    if len(city_ls) != len(count_ls):
        raise ValueError("城市列表和计数列表的长度必须相同")

    # Use Counter for efficient counting
    province_counts = Counter()
    province_counts.update(
        {city2province[loc]: count for loc, count in zip(city_ls, count_ls)}
    )

    # Sort provinces by count (descending) and then by name
    sorted_provinces = sorted(province_counts.items(), key=lambda x: (-x[1], x[0]))
    provinces, counts = zip(*sorted_provinces)

    return list(provinces), list(counts)
