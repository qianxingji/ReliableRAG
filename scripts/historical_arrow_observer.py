"""Observation-only pq argument: real Arrow IO, selected answer scalars only."""
from pathlib import Path


class ObservedParquet:
    def __init__(self, parquet, wanted, allowed_paths):
        self.parquet=parquet;self.wanted=set(wanted);self.allowed_paths={Path(x).resolve() for x in allowed_paths}
        self.calls=[];self.python_answer_scalars=0;self.identifiers=0;self.denied=[]

    def reject(self,reason):
        self.denied.append(reason);raise RuntimeError(reason)

    def ParquetFile(self,handle):
        if not hasattr(handle,'name') or Path(handle.name).resolve() not in self.allowed_paths:self.reject('UNBOUND_PARQUET_HANDLE')
        return ObservedFile(self,self.parquet.ParquetFile(handle))

    def receipt(self):
        return dict(real_pyarrow=True,calls=self.calls,selected_answer_python_scalars=self.python_answer_scalars,
            source_identifier_python_values=self.identifiers,denied=list(self.denied),
            unselected_reference_python_values_materialized=0,physical_page_decompression_may_include_unselected_rows=True)


class ObservedFile:
    def __init__(self,observer,actual):self.observer=observer;self.actual=actual;self.selected={}
    @property
    def schema_arrow(self):return self.actual.schema_arrow
    @property
    def num_row_groups(self):return self.actual.num_row_groups
    def read_row_group(self,index,*,columns,use_threads,use_pandas_metadata):
        if columns not in (['id'],['answer']) or use_threads is not False or use_pandas_metadata is not False:self.observer.reject('FORBIDDEN_PARQUET_COLUMN_OR_OPTION')
        if columns==['answer'] and not self.selected.get(index):self.observer.reject('ANSWER_BEFORE_SELECTED_ID_PASS')
        self.observer.calls.append(dict(row_group=index,columns=list(columns),use_threads=use_threads,use_pandas_metadata=use_pandas_metadata))
        actual=self.actual.read_row_group(index,columns=columns,use_threads=use_threads,use_pandas_metadata=use_pandas_metadata)
        return ObservedTable(self,actual,index,columns[0])


class ObservedTable:
    def __init__(self,parent,actual,index,column):self.parent=parent;self.actual=actual;self.index=index;self.column_name=column
    def column(self,name):
        if name!=self.column_name:self.parent.observer.reject('UNREQUESTED_PARQUET_COLUMN')
        return ObservedColumn(self.parent,self.actual.column(name),self.index,name)


class ObservedColumn:
    def __init__(self,parent,actual,index,name):self.parent=parent;self.actual=actual;self.index=index;self.name=name
    def to_pylist(self):
        if self.name!='id':self.parent.observer.reject('WHOLE_ANSWER_COLUMN_PYTHON_CONVERSION')
        ids=self.actual.to_pylist();self.parent.observer.identifiers+=len(ids)
        self.parent.selected[self.index]={i for i,value in enumerate(ids) if value in self.parent.observer.wanted}
        return ids
    def __getitem__(self,index):
        if self.name!='answer' or type(index)is not int or index not in self.parent.selected.get(self.index,set()):self.parent.observer.reject('UNSELECTED_ANSWER_SCALAR')
        return ObservedScalar(self.parent.observer,self.actual[index])


class ObservedScalar:
    def __init__(self,observer,actual):self.observer=observer;self.actual=actual
    def as_py(self):
        self.observer.python_answer_scalars+=1;return self.actual.as_py()
