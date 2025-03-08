import pandas as pd
from typing import List, Union, Optional

from utils import get_csvdf, parse_date


# Define pensafe directory constant
pensafe = "safe"


def get_safedetail(orgname: str = "") -> pd.DataFrame:
    """
    Get safety detail data, optionally filtered by organization.
    
    Args:
        orgname: Organization name to filter by (optional)
        
    Returns:
        DataFrame containing safety details
    """
    beginwith = "safedtl"
    pendf = get_csvdf(pensafe, beginwith)
    
    if orgname:
        pendf = pendf[pendf["区域"] == orgname]
        
    if len(pendf) > 0:
        pendf.loc[:, "发布日期"] = pendf["date"].apply(parse_date)

    return pendf


def searchsafe(
    df: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    wenhao_text: str,
    people_text: str,
    event_text: str,
    penalty_text: str,
    org_text: str,
    province: List[str],
    min_penalty: float = 0,
) -> pd.DataFrame:
    """
    Search safety records based on multiple criteria.
    
    Args:
        df: Source DataFrame
        start_date: Start date for search range
        end_date: End date for search range
        wenhao_text: Text to search in document numbers
        people_text: Text to search in person/entity names
        event_text: Text to search in violation descriptions
        penalty_text: Text to search in penalty descriptions
        org_text: Text to search in organization names
        province: List of provinces to include
        min_penalty: Minimum penalty amount
        
    Returns:
        DataFrame with filtered search results
    """
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
    ]
    
    # Sort by date in descending order
    searchdf = searchdf.sort_values(by=["发布日期"], ascending=False)
    searchdf = searchdf.reset_index(drop=True)
    
    return searchdf