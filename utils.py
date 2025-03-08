import os
import glob
import datetime
import pandas as pd

from typing import Optional, List, Union


def get_csvdf(penfolder: str, beginwith: str) -> pd.DataFrame:
    """
    Read and concatenate multiple CSV files with filenames starting with specific prefix.
    
    Args:
        penfolder: Directory path to search in
        beginwith: String prefix for CSV filenames to match
    
    Returns:
        Concatenated DataFrame of all matching CSV files or empty DataFrame if none found
    """
    files2 = glob.glob(penfolder + "**/" + beginwith + "*.csv", recursive=True)
    dflist = []
    
    for filepath in files2:
        pendf = pd.read_csv(filepath, index_col=0)
        dflist.append(pendf)
        
    if len(dflist) > 0:
        df = pd.concat(dflist)
        df.reset_index(drop=True, inplace=True)
    else:
        df = pd.DataFrame()
        
    return df


def parse_date(date_string: str) -> Optional[datetime.date]:
    """
    Parse date string in various formats to datetime.date object.
    
    Args:
        date_string: String containing a date
        
    Returns:
        datetime.date object or None if parsing fails
    """
    try:
        return pd.to_datetime(date_string, format="%Y/%m/%d").date()
    except ValueError:
        try:
            return pd.to_datetime(date_string, format="%Y-%m-%d").date()
        except ValueError:
            # Add more formats as needed
            return None


def savedf(df: pd.DataFrame, basename: str) -> None:
    """
    Save DataFrame to CSV in the pensafe directory.
    
    Args:
        df: DataFrame to save
        basename: Base filename (without .csv extension)
    """
    savename = basename + ".csv"
    savepath = os.path.join(pensafe, savename)
    df.to_csv(savepath)


def get_now() -> str:
    """
    Get current datetime as formatted string.
    
    Returns:
        Current datetime as string in format 'YYYYMMDDHHMMSS'
    """
    now = datetime.datetime.now()
    now_str = now.strftime("%Y%m%d%H%M%S")
    return now_str


# Define pensafe directory constant
pensafe = "safe"