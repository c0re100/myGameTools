from collections import namedtuple
import time
from typing import Dict, Union
from urllib.parse import urlparse, urlunparse
import sqlite3
import json


def apiDataCrypt(data: bytes, key: bytes):
    encrypted = bytearray()
    for i in range(len(data)):
        byte = data[i]
        key_byte = key[i % len(key)]
        encrypted.append(byte ^ key_byte)
    return bytes(encrypted)


def setmitmRealDataProp():  # 检测realData是否修改
    @property
    def realData(self):
        return self._realData

    @realData.setter
    def realData(self, value):
        if hasattr(self, 'realData'):
            self.realDataIsModified = True
        else:
            self.realDataIsModified = False
        self._realData = value
    return realData


apiConfig = namedtuple('apiConfig', ['isOverwrite', 'isHaveField', 'funcReq', 'funcResp'], defaults=[False, False, False, False])


def getApiData(urlpath, datatable='apiinfo', sid=None) -> dict | str:
    conn = sqlite3.connect(f"{database_name}.db")
    cursor = conn.cursor()
    if sid is not None:
        cursor.execute(f"SELECT apiData FROM {datatable} WHERE apiPath = ? AND sid = ?", (urlpath, sid))
    else:
        cursor.execute(f"SELECT apiData FROM {datatable} WHERE apiPath = ?", (urlpath,))

    apidata = cursor.fetchone()
    if apidata:
        try:
            return json.loads(apidata[0])
        except json.JSONDecodeError:
            return apidata[0]
    else:
        return None


def getApiDataSidAll(urlpath, datatable='apiinfo'):
    conn = sqlite3.connect(f"{database_name}.db")
    cursor = conn.cursor()

    cursor.execute(f"SELECT sid, apiData FROM {datatable} WHERE apiPath = ?", (urlpath,))
    results = cursor.fetchall()

    data_with_sid = {}
    for result in results:
        sid, apidata = result
        try:
            data_with_sid[sid] = json.loads(apidata)
        except json.JSONDecodeError:
            data_with_sid[sid] = apidata

    conn.close()
    return data_with_sid


def saveApiData(urlpath, data: str, isOverwrite=False, datatable='apiinfo', SPid=None, isFakeData=False, dataName2nd='apiPath', dataName1st='apiData'):
    conn = sqlite3.connect(f"{database_name}.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT {dataName1st} FROM {datatable} WHERE {dataName2nd} = ?", (urlpath,))
    existing_url = cursor.fetchone()

    if existing_url:
        if isOverwrite:
            cursor.execute(f"UPDATE {datatable} SET {dataName1st} = ? WHERE {dataName2nd} = ?", (data, urlpath))
    else:
        cursor.execute(f"INSERT INTO {datatable} ({dataName2nd}, {dataName1st}) VALUES (?, ?)", (data, urlpath))

    conn.commit()
    conn.close()


def saveApiData2(urlpath, data: str | dict, isOverwrite=False, datatable='apiinfo', SPid=None, isFakeData=None, dataName2nd='apiPath', dataName1st='apiData'):
    if isinstance(data, dict):
        data = json.dumps(data)

    conn = sqlite3.connect(f"{database_name}.db")
    cursor = conn.cursor()

    if SPid is not None:
        cursor.execute(f"SELECT {dataName1st} FROM {datatable} WHERE sid = ? AND {dataName2nd} = ?", (SPid, urlpath))
    else:
        cursor.execute(f"SELECT {dataName1st} FROM {datatable} WHERE {dataName2nd} = ?", (urlpath,))
    existing_record = cursor.fetchone()

    if existing_record:
        if SPid is not None:
            if isOverwrite:
                cursor.execute(f"UPDATE {datatable} SET {dataName1st} = ? WHERE sid = ? AND {dataName2nd} = ?", (data, SPid, urlpath))
                if isFakeData:
                    cursor.execute(f"UPDATE {datatable} SET isFakeData = 1 WHERE sid = ? AND {dataName2nd} = ?", (SPid, urlpath))
        else:
            if isOverwrite:
                cursor.execute(f"UPDATE {datatable} SET {dataName1st} = ? WHERE {dataName2nd} = ?", (data, urlpath))
                if isFakeData:
                    cursor.execute(f"UPDATE {datatable} SET isFakeData = 1  WHERE {dataName2nd} = ?", (urlpath))
    else:
        cursor.execute(f"INSERT INTO {datatable} ({dataName2nd}, {dataName1st}, sid, isFakeData) VALUES (?, ?, ?, ?)", (urlpath, data, SPid, 1 if isFakeData else 0))
    conn.commit()
    conn.close()


def saveApiDataSidAll(urlpath, data_with_sid: dict, datatable='apiinfo'):
    conn = sqlite3.connect(f"{database_name}.db")
    cursor = conn.cursor()
    for sid, data in data_with_sid.items():
        if isinstance(data, dict) or isinstance(data, list):
            data = json.dumps(data)

        # 检查是否存在相同的apiPath和sid记录
        cursor.execute(f"SELECT COUNT(*) FROM {datatable} WHERE apiPath=? AND sid=?", (urlpath, sid))
        count = cursor.fetchone()[0]

        if count > 0:
            # 如果存在，则更新对应的apiData
            cursor.execute(f"UPDATE {datatable} SET apiData=? WHERE apiPath=? AND sid=?", (data, urlpath, sid))
        else:
            # 如果不存在，则插入新记录
            cursor.execute(f"INSERT INTO {datatable} (apiPath, apiData, sid) VALUES (?, ?, ?)", (urlpath, data, sid))

    conn.commit()
    conn.close()


def get_storylist_by_unitid(unitid):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(f'{database_name}.db')
    cursor = conn.cursor()

    # 执行查询以获取指定 unitid 的 storylist
    cursor.execute("SELECT storylist FROM charalist WHERE unit_id = ?", (unitid,))
    result = cursor.fetchone()

    # 关闭连接
    conn.close()

    # 如果找到了记录，则返回 storylist；否则返回 None
    if result:
        return result[0]
    else:
        return None


defaultresponseData = json.dumps({

})

defaultresponseHeader = {
    'X-Access-Token': '1:1:a',
    'X-Game-Token': 'a',
    'Content-Type': 'application/json; charset="UTF-8"',
    'Access-Control-Allow-Origin': '*'
}
