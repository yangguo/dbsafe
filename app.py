import pandas as pd
import streamlit as st

# from docx2pdf import convert


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
)


temppath = "temp"

# set page config
st.set_page_config(
    page_title="外管局监管处罚分析",
    page_icon=":bank:",
    layout="wide",
    initial_sidebar_state="expanded",
)

cityls = [
    "北京",
    "厦门",
    "青海",
    "甘肃",
    "天津",
    "河北",
    "贵州",
    "湖南",
    "深圳",
    "江西",
    "广东",
    "重庆",
    "黑龙江",
    "福建",
    "河南",
    "陕西",
    "海南",
    "云南",
    "湖北",
    "山东",
    "新疆",
    "宁波",
    "大连",
    "江苏",
    "内蒙古",
    "浙江",
    "吉林",
    "广西",
    "上海",
    "宁夏",
    "安徽",
    "山西",
    "青岛",
    "辽宁",
    "西藏",
    "四川",
    "总部",
]


def main():
    menu = [
        "案例总数",
        "案例搜索",
        "案例更新",
        "附件处理",
        "案例下载",
        "案例上线",
    ]

    choice = st.sidebar.selectbox("选择", menu)

    if choice == "案例总数":
        st.subheader("案例总数")

        display_summary()

    elif choice == "案例更新":
        st.subheader("案例更新")

        # choose orgname index
        org_name_ls = st.sidebar.multiselect("机构", cityls)
        if org_name_ls == []:
            org_name_ls = cityls

        # set org_name_ls to session state
        st.session_state["org_name_ls"] = org_name_ls

        # checkbox to filter pending org_name_list
        pendingorg = st.sidebar.checkbox("待更新机构")
        if pendingorg:
            # get pending org_name list
            org_name_ls = toupt_safesum(org_name_ls)
            # display pending org_name list
            st.markdown("#### 待更新机构")
            # convert list to string
            orglsstr = ",".join(org_name_ls)
            st.markdown(" #### " + orglsstr)
        # st.write(org_name_ls)
        display_safesum(org_name_ls)

        # choose page start number and end number
        start_num = st.sidebar.number_input("起始页", value=1, min_value=1)
        # convert to int
        start_num = int(start_num)
        end_num = st.sidebar.number_input("结束页", value=1)
        # convert to int
        end_num = int(end_num)
        # button to scrapy web
        sumeventbutton = st.sidebar.button("更新列表")

        if sumeventbutton:
            for org_name in org_name_ls:
                # write org_name
                st.markdown("#### 更新列表：" + org_name)

                start = start_num
                end = end_num

                while True:
                    # get sumeventdf
                    sumeventdf = get_sumeventdf(org_name, start, end)
                    # get length of sumeventdf
                    length = len(sumeventdf)
                    # display length
                    st.success(f"获取了{length}条案例")
                    # update sumeventdf
                    newsum = update_sumeventdf(sumeventdf, org_name)
                    # get length of newsum
                    sumevent_len = len(newsum)
                    # display sumeventdf
                    st.success(f"共{sumevent_len}条案例待更新")

                    if sumevent_len == length and length > 0:
                        start = end + 1
                        end = end + 1
                        continue
                    else:
                        break

        # update detail button
        eventdetailbutton = st.sidebar.button("更新详情")
        if eventdetailbutton:
            for org_name in org_name_ls:
                # write org_name
                st.markdown("#### 更新详情：" + org_name)
                # update sumeventdf
                newsum = update_toupd(org_name)
                # get length of toupd
                newsum_len = len(newsum)
                # display sumeventdf
                st.success(f"共{newsum_len}条案例待更新")
                if newsum_len > 0:
                    # get toupdate list
                    toupd = get_safetoupd(org_name)
                    st.write(toupd)
                    # get event detail
                    eventdetail = get_eventdetail(toupd, org_name)
                    # get length of eventdetail
                    eventdetail_len = len(eventdetail)
                    # display eventdetail
                    st.success(f"更新完成，共{eventdetail_len}条案例详情")
                else:
                    st.error("没有更新的案例")

        # button to refresh page
        refreshbutton = st.sidebar.button("刷新页面")
        if refreshbutton:
            st.experimental_rerun()

    elif choice == "案例搜索":
        st.subheader("案例搜索")

        if "search_result_safe" not in st.session_state:
            st.session_state["search_result_safe"] = None
        if "keywords_safe" not in st.session_state:  # 生成word的session初始化
            st.session_state["keywords_safe"] = []

        # resls = []
        dfl = get_safedetail("")
        # st.write(dfl)
        # st.write(dfl['区域'].unique().tolist())
        # st.write(dfl.isnull().sum())
        # get min and max date of old eventdf
        min_date = dfl["发布日期"].min()
        max_date = dfl["发布日期"].max()

        # loclist = dfl["区域"].unique().tolist()
        loclist = cityls
        # one years ago
        one_year_ago = max_date - pd.Timedelta(days=365 * 1)

        # use form
        with st.form("搜索案例"):
            col1, col2 = st.columns(2)

            with col1:
                # input date range
                start_date = st.date_input(
                    "开始日期", value=one_year_ago, min_value=min_date
                )
                # input wenhao keyword
                wenhao_text = st.text_input("文号关键词")
                # input people keyword
                people_text = st.text_input("当事人关键词")
                # input event keyword
                event_text = st.text_input("案情关键词")
            with col2:
                end_date = st.date_input("结束日期", value=max_date, min_value=min_date)
                # input penalty keyword
                penalty_text = st.text_input("处罚决定关键词")
                # input org keyword
                org_text = st.text_input("处罚机关关键词")
                # choose province using multiselect
                province = st.multiselect("处罚区域", loclist)
            # search button
            searchbutton = st.form_submit_button("搜索")

        if searchbutton:
            # if text are all empty
            if (
                wenhao_text == ""
                and people_text == ""
                and event_text == ""
                # and law_text == ""
                and penalty_text == ""
                and org_text == ""
            ):
                st.warning("请输入搜索关键词")
            if province == []:
                province = loclist
            st.session_state["keywords_safe"] = [
                start_date,
                end_date,
                wenhao_text,
                people_text,
                event_text,
                penalty_text,
                org_text,
                province,
            ]
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
            )
            # save search_df to session state
            st.session_state["search_result_safe"] = search_df
        else:
            search_df = st.session_state["search_result_safe"]

        if search_df is None:
            st.error("请先搜索")
            st.stop()

        if len(search_df) > 0:
            # display eventdetail
            display_eventdetail(search_df)
        else:
            st.warning("没有搜索结果")

    elif choice == "案例下载":
        download_safesum()

    # elif choice == "案例上线":
    #     uplink_safesum()


if __name__ == "__main__":
    main()
