import re
import logging
from datetime import datetime

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)

class CheckParenthesees:
    def __init__(self):
        self.file = None

    def get_text_split_separatorfromregex(self,text_to_sep,pattern='[({})]'):
        """Returns the text before the first encounter of a separator (in the pattern) from a text.

        Args:
            text_to_sep (str): text to separate
            pattern (str, optional): Separator. Defaults to '[({})]'.

        Returns:
            str: Text before any separator in pattern
        """
        ppp=re.findall(text_to_sep,pattern)
        if len(ppp)>0:
            return ppp[0] #separate first
        return text_to_sep
    
    def nums_parenthesees(self,txt,ini_p,end_p):
        """counts the number of parenthesees in a text

        Args:
            txt (str): text to search
            ini_p (str): count of opening
            end_p (str): count of closing

        Returns:
            tuple: (number opening,number closing)
        """
        _,no_p_ini=self.split_text(ini_p,txt) 
        _,no_p_end=self.split_text(end_p,txt) 
        #log.error(no_p_ini,no_p_end)
        return [no_p_ini,no_p_end]
    
    def split_text(self,separator,line):
        """Splits a text line by the separator

        Args:
            separator (str): separator to split text
            line (str): text to be splitted

        Returns:
            tuple(list,int): (text part list, number of parts)
        """
        alist=[]
        count=0
        try:                                      
            mf =re.split(separator,line)                               
            x=re.findall(separator,line)
        except:
            mf = None
        try:
            if mf is not None:                  
                for item in mf:                                   
                    alist.append(item)
                if x is not None:
                    count=len(x)     
            else:
                alist.append(line)
        except Exception as e:            
            log.error(e)  
            log.error('split text')                      
            alist=[]
            pass
        return alist,count      
    
    def check_parenthesees_in_one_format(self,a_format:str)->bool:
        """checks in [({})] parenthesees that the correct number of openings and closings 
        are the same and that they are not entangled.

        Args:
            a_format (str): text to be checked

        Returns:
            bool: True if parenthesees ok
        """
        allok=True
        a_for=str(a_format)
        if not self.check_one_parenthesees(a_for,ini_p=r'\[',end_p=r'\]',logerr=False):
            log.error('Parenthesees Mismatch "[ ]" in Format <'+ a_for+'>')
            allok=False
        if not self.check_one_parenthesees(a_for,ini_p=r'\(',end_p=r'\)',logerr=False):
            log.error('Parenthesees Mismatch "( )" in Format <'+ a_for+'>')
            allok=False
        if not self.check_one_parenthesees(a_for,ini_p=r'\{',end_p=r'\}',logerr=False):
            log.error('Parenthesees Mismatch "{ }" in Format <'+ a_for+'>')
            allok=False
        if allok:           
            if not self.check_entangled_parenthesees(a_for,logerr=False):
                log.error('Parenthesees Entangled {[( }]) in Format <'+ a_for+'>')
                allok=False
        return allok

    def format_which_inside_parenthesees(self,a_format,ini_p=r'\[',end_p=r'\]',pattern='[({})]'):
        """Gets the text inside sequences

        Args:
            a_format (_type_): _description_
            ini_p (regexp, optional): Regex opening sequence. Defaults to r'\['.
            end_p (regexp, optional): Regex closing sequence. Defaults to r'\]'.
            pattern (str, optional): Separators. Defaults to '[({})]'.

        Returns:
            tuple(list[str],int): (list of texts in between openings, number of openings)
        """
        a_format=str(a_format)
        try:
            alist=[]
            ini_sep=self.get_text_split_separatorfromregex(ini_p,pattern)
            end_sep=self.get_text_split_separatorfromregex(end_p,pattern)
            _,no_p_ini=self.split_text(ini_p,a_format) 
            _,no_p_end=self.split_text(end_p,a_format) 
            #print(no_p_ini,no_p_end)
            if no_p_ini!=no_p_end:
                log.error('Bad Format '+ini_sep+' '+end_sep+' in <'+a_format+'>')   
            txt=str(a_format)                             
            alist=self.get_list_in_between_txt(txt,ini_sep,end_sep)    
            no_p_ini=len(alist)              
        except Exception as e:            
            log.error(e)     
            log.error('Inside Parentheses')                        
            alist=[]
            no_p_ini=0
            pass            
        return alist,no_p_ini

    def get_list_in_between_txt(self,txt,inis,ends):
        """Gets a sequential list of texts in between the openings and closings

        Args:
            txt (str): text
            inis (str): opening
            ends (str): closing

        Returns:
            list[str]: list of texts in between
        """
        alist=[]
        astr=''
        doappend=False
        count=0
        for achar in txt:
            if achar==ends and inis!=ends:
                doappend=False
            if achar==inis and inis!=ends:
                doappend=True
                count=count+1
            if inis==ends and achar==ends:
                doappend= not doappend   
            if doappend:
                if achar!=inis and achar!=ends:
                    astr=astr+achar    
            if  doappend==False and count>=1:
                alist.append(astr)
                astr=''
                count=0
        return alist        

    def check_entangled_parenthesees(self,txt:str,logerr:bool=False)->bool:
        """Checks for entanglement in parenthesees.

        Args:
            txt (str): text
            logerr (bool, optional): log when true. Defaults to False.

        Returns:
            _type_: _description_
        """
        p1list,_=self.format_which_inside_parenthesees(txt,r'\{',r'\}')  
        [np1ini,np1end]=self.nums_parenthesees(txt,r'\{',r'\}')
        [np2ini,np2end]=self.nums_parenthesees(txt,r'\[',r'\]')
        [np3ini,np3end]=self.nums_parenthesees(txt,r'\(',r'\)')
        if np1ini==np1end and np2ini==np2end and np3ini==np3end:
            if np1ini==0 and np2ini==0 and np3ini==0:
                return True
            if np1ini>0 and np2ini==0 and np3ini==0:
                return True    
            if np1ini==0 and np2ini>0 and np3ini==0:
                return True
            if np1ini==0 and np2ini==0 and np3ini>0:
                return True    
            if np1ini>0 and np2ini>0:
                p1list,_=self.format_which_inside_parenthesees(txt,r'\{',r'\}') 
                for ppp1 in p1list:
                    #log.error('+1 depth')
                    if txt!=ppp1:
                        isok=self.check_entangled_parenthesees(ppp1,False)
                    if not isok:
                        return False
            elif np2ini>0 and np3ini>0:
                p2list,_=self.format_which_inside_parenthesees(txt,r'\[',r'\]') 
                for ppp2 in p2list:
                    #log.error('+2 depth')
                    if txt!=ppp2:
                        isok=self.check_entangled_parenthesees(ppp2,False)
                    if not isok:
                        return False          
                return True    
            elif np1ini>0 and np3ini>0:
                p3list,_=self.format_which_inside_parenthesees(txt,r'\(',r'\)') 
                for ppp3 in p3list:
                    if txt!=ppp3:
                        isok=self.check_entangled_parenthesees(ppp3,False)
                    if not isok:
                        return False        
                return True                    
        if logerr:
            log.error('Different amounts of opening and closing Parenthesees')
        return False

    def check_one_parenthesees(self,a_format,ini_p=r'\[',end_p=r'\]',logerr=True):
        """Check whether text inside sequences is correctly formatted.

        Args:
            a_format (str): text
            ini_p (regexp, optional): regex opening sequence. Defaults to r'\['.
            end_p (regexp, optional): regex closing sequence. Defaults to r'\]'.
            logerr (bool, optional): Log. Defaults to True.

        Returns:
            _type_: _description_
        """
        a_format=str(a_format)
        try:            
            ini_sep=self.get_text_split_separatorfromregex(ini_p)
            end_sep=self.get_text_split_separatorfromregex(end_p)
            [no_p_ini,no_p_end]=self.nums_parenthesees(a_format,ini_p,end_p)
            if no_p_ini!=no_p_end:
                if logerr:
                    log.error('Bad Format '+ini_sep+' '+end_sep+' in <'+a_format+'>')
                return False
            return True
        except:
            log.error('Bad Parenthesees Format '+ini_sep+' '+end_sep+' in <'+a_format+'>')
            pass
        return False

# chp=CheckParenthesees()
# from rich import print

# id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6	'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9

ALLOWED_OPERATORS_DICT={'=':"Like (case sensitive), use * or % as wildcard",
                        '~=':"Like (Not case sensitive), use * or % as wildcard",
                        '==':"Exactly equal (use % wildcards)",
                        '!=':"Not like, use * or % as wildcard",
                        '<>':"Exactly not (use % wildcards)",
                        '>':"Greater than",
                        '>=':"Greater than or equal",
                        '<':"Less than",
                        '<=':"Less than or equal",
                        '||':"Or",
                        '&&':"And",
                        }
ALLOWED_OPERATORS=list(ALLOWED_OPERATORS_DICT.keys())
ALLOWED_DICT={"id":{'operators':['!=','<>','=','==','>=','<=','<','>'],'format':str(int)},
              "dt_data_created":{'operators':['!=','<>','=','==','>=','<=','<','>'],'format':str(datetime)}, 
              "dt_data_modified":{'operators':['!=','<>','=','==','>=','<=','<','>'],'format':str(datetime)}, 
              "filepath":{'operators':['!=','<>','=','==','~=','||','&&'],'format':str(str)}, 
              "filename":{'operators':['!=','<>','=','==','~=','||','&&'],'format':str(str)},
              "md5":{'operators':['!=','<>','=','==','~='],'format':str(str)},
              "size":{'operators':['!=','<>','=','==','>=','<=','<','>','~='],'format':str(float)},
              "dt_file_created":{'operators':['!=','<>','=','==','>=','<=','<','>','~='],'format':str(datetime)},
              'dt_file_accessed':{'operators':['!=','<>','=','==','>=','<=','<','>','~='],'format':str(datetime)},
              "dt_file_modified":{'operators':['!=','<>','=','==','>=','<=','<','>','~='],'format':str(datetime)},
              }
ALLOWED_OPERATIONS=list(ALLOWED_DICT.keys())

class SQLSearchGenerator:
    def __init__(self):
        self.options = ""
        self.chp=CheckParenthesees()

    def parse_query_operator(self,input_str):
        """
        Parse a string in the format "filename=operator=query_text" or just filename.
        
        Args:
            input_str (str): The input string to be parsed.

        Returns:
            dict: A dictionary containing the operation, operator, and query text if 'operator' is provided,
                otherwise None for all three fields.
        """
        has_operator=False
        for operator in ALLOWED_OPERATORS:
            if operator in input_str:
                has_operator=True
                break
        if not has_operator:
            return {'operation': None, 'operator': None, 'query_text': input_str}
        # Regular expression pattern to match "filename=operator=query_text"
        pattern_double = r"(.*)((?:==|!=|>=|<=|<>|&&|\|\||~=))(.*)"
        pattern_single = r"(.*)((?:=|>|<))(.*)"
        match = re.match(pattern_double, input_str)
        if match:
            operation = match.group(1)
            operator = match.group(2).strip()
            query_text = match.group(3).strip()
            rec_dict=self.parse_query_operator(operation)
            if rec_dict['operation']:
                return {'operation': rec_dict['operation'], 'operator': rec_dict['operator'], 'query_text': rec_dict['query_text']+ operator +query_text}
            return {'operation': operation, 'operator': operator, 'query_text': query_text}
        match = re.match(pattern_single, input_str)
        if match:
            operation = match.group(1)
            operator = match.group(2).strip()
            query_text = match.group(3).strip()
            rec_dict=self.parse_query_operator(operation)
            if rec_dict['operation']:
                return {'operation': rec_dict['operation'], 'operator': rec_dict['operator'], 'query_text': rec_dict['query_text']+ operator +query_text}
            return {'operation': operation, 'operator': operator, 'query_text': query_text}
        # Nothing found
        return {'operation': None, 'operator': None, 'query_text': None}

    @staticmethod
    def remove_empty_queries(query_list:list[str])->list:
        """Removes empty queries

        Args:
            query_list (list[str]): a query list

        Returns:
            list: query list without empty queries
        """
        aql=query_list.copy()
        for iii,a_query in enumerate(aql):
            if a_query.strip()=='':
                query_list.pop(iii)
        return query_list

    def get_sub_queries(self,main_query_list:list[str],sub_query_dict:dict=None)->tuple:
        """Replaces sub queries with __sub_query#__ respectively in the query list.
        Returns Modified query list and dictionaries with queries

        Args:
            main_query_list (list[str]): query list
            sub_query_dict (dict, optional): Sub query dictionary to append. Defaults to None.

        Returns:
            tuple: [list,dict]:(modified query list, sub query dict)
        """
        #Get sub queries
        if not sub_query_dict:
            sub_query_dict={}
        for jjj,a_query in enumerate(main_query_list):
            sub_query_list,_=self.chp.format_which_inside_parenthesees(a_query,r"\(",r"\)")
            for iii,a_sub_query in enumerate(sub_query_list):
                sub_query_dict.update({f"__sub_query{jjj+iii}__":f"({a_sub_query})"})
        #Replace sub queries
        mql=main_query_list.copy()
        for jjj,a_query in enumerate(mql):
            for akey,value in sub_query_dict.items():
                if value in a_query:
                    main_query_list[jjj]=main_query_list[jjj].replace(value,akey) #f"__sub_query{akey}__")
        sep_sub_query_dict={}
        for akey,value in sub_query_dict.items():
            sep_list=self.chp.get_list_in_between_txt(value,"(",")")
            sep_sub_query_dict.update({akey:sep_list})
        return main_query_list, sep_sub_query_dict

    def get_and_or_dictionaries(self,the_query_list:list,and_dict:dict=None,or_dict:dict=None)->tuple:
        """Replaces AND and OR queries with __and_query#__ or __or_query#__ respectively in the query list.
        returns Modified list and dictionaries with querries

        Args:
            the_query_list (list): _description_
            and_dict (dict, optional): AND dictionary to append more queries. Defaults to None.
            or_dict (dict, optional): OR dictionary to append more queries. Defaults to None.

        Returns:
            tuple[list,dict,dict]:(modified_list, AND dict, OR dict)
        """
        aql=the_query_list.copy()
        if not and_dict:
            and_dict={}
        if not or_dict:
            or_dict={}
        kkk=len(and_dict)
        jjj=len(or_dict)
        for iii,a_query in enumerate(aql):
            if '&&' in a_query:
                a_query_list,_=self.chp.split_text(r'\&\&',a_query)
                and_dict.update({f'__and_query{kkk}__':a_query_list})
                the_query_list[iii]=f'__and_query{kkk}__'
                kkk=kkk+1
                # print('and splitted->',a_query_list)
            if '||' in a_query:
                a_query_list,_=self.chp.split_text(r'\|\|',a_query)
                or_dict.update({f'__or_query{jjj}__':a_query_list})
                the_query_list[iii]=f'__or_query{jjj}__'
                jjj=jjj+1
                # print('or splitted->',a_query_list)
        return the_query_list, and_dict, or_dict

    @staticmethod
    def get_datetime_text(q_txt:str)->tuple:
        """Gets formated datetime"""
        try:
            dt=datetime.fromisoformat(q_txt)
            return dt,True
        except (NameError,ValueError,TypeError):
            pass
        ########## TODO -> add time only format
        return '',False

    @staticmethod
    def is_time_hhmmss_format(input_str:str)->tuple:
        """Gets a string with format hh:mm:ss 

        Args:
            input_str (str): string

        Returns:
            tuple: match string, True if hh:mm:ss format
        """
        # Define units to convert from
        input_str=input_str.strip().lower()
        # Regular expression patterns for different input formats
        pattern_hhmmss = r'((?:[2][0-3]|[0-1]\d):[0-5]\d:[0-5]\d(?:\.)?(?:\d+)?)'
        match = re.match(pattern_hhmmss, input_str)
        if match:
            return  str(match.group(1)), True
        return input_str,False
    
    @staticmethod
    def is_date_yyyymmdd_format(input_str:str)->tuple:
        """Gets a string with format hh:mm:ss 

        Args:
            input_str (str): string

        Returns:
            tuple: match string, True if hh:mm:ss format
        """
        # Define units to convert from
        input_str=input_str.strip().lower()
        input_str=input_str.replace('*','%')
        # Regular expression patterns for different input formats
        pattern_yyyymmdd = r'((\d\d\d\d)-(?:[1][0-2]|0\d)-(?:[3][0-1]|[0-2]\d))$'
        pattern_yyyy = r'([%]?\d\d\d\d[%]?)$'
        pattern_yyyymm = r'([%]?(\d\d\d\d)-(?:[1][0-2]|0\d)[%]?)$'
        pattern_mmdd = r'([%]?-(?:[1][0-2]|0\d)-(?:[3][0-1]|[0-2]\d)[%]?)$'
        pattern_mm = r'([%]?-(?:[1][0-2]|0\d)-[%]?)$'
        pattern_dd = r'([%]?-(?:[3][0-1]|[0-2]\d)[%]?)$'
        match = re.match(pattern_yyyy, input_str)
        if match:
            adate=str(match.group(1))
            if '0000' in adate:
                return input_str,False 
            return  adate, True
        match = re.match(pattern_mm, input_str)
        if match:
            adate=str(match.group(1))
            return  adate, True
        match = re.match(pattern_dd, input_str)
        if match:
            adate=str(match.group(1))
            return  adate, True
        is_match=False
        match = re.match(pattern_mmdd, input_str)
        if match:
            adate=str(match.group(1))
            adate_sp=['3333']+adate.replace('%','').split('-')
            is_match=True
        match = re.match(pattern_yyyymm, input_str)
        if match:
            adate=str(match.group(1))
            adate_sp=adate.replace('%','').split('-')+['03']   
            is_match=True
        match = re.match(pattern_yyyymmdd, input_str)
        if match:
            adate=str(match.group(1))
            adate_sp=adate.split('-')
            is_match=True
        if is_match:
            if adate.startswith('0000'):
                return input_str,False 
            # 30 day months
            if adate_sp[1]in ['04','06','09','11'] and int(adate_sp[2])>30:
                return input_str,False 
            # February
            _,rem=divmod(int(adate_sp[0]),4)   
            if adate_sp[1]=='02' and int(adate_sp[2])>28 and rem!=0:
                return input_str,False 
            if adate_sp[1]=='02' and int(adate_sp[2])>29 and rem==0:
                return input_str,False 
            return  adate, True
        return input_str,False

    def check_dt_type(self,q_txt:str)->bool:
        """Chech if it has a datetime or number format"""
        # if its time
        _,is_time=self.is_time_hhmmss_format(q_txt)
        if is_time:
            return True
        _,is_date=self.is_date_yyyymmdd_format(q_txt)
        if is_date:
            return True
        # if its a date
        try:
            _=datetime.fromisoformat(q_txt)
            return True
        except (NameError,ValueError,TypeError):
            pass
        ########## TODO -> add time only format regex?
        try:
            _=float(q_txt)
        except (ValueError,TypeError):
            return False
        return True   

    @staticmethod
    def separate_file_size_value_and_unit(input_str:str)->tuple:
        """Gets a string with bytes an units into a value unit tuple.
        Valid units: bytes|by|kb|mb|gb|tb|er

        Args:
            input_str (str): value or value with units

        Returns:
            _type_: value,unit
        """
        # Define units to convert from
        input_str=input_str.strip().lower()
        # Regular expression patterns for different input formats
        pattern_float = r'(-?\d+(?:\.)?(?:\d+)?)'
        pattern_unit=r"(-?\d+(?:\.)?(?:\d+)?)((?:bytes|by|kb|mb|gb|tb|er|))"

        match = re.match(pattern_unit, input_str)
        if match:
            if len(match.groups())>1:
                value = float(match.group(1))
                unit = str(match.group(2))
                return value,unit
        match = re.match(pattern_float, input_str)
        if match:
            value = float(match.group('value'))
            unit = None
            return value,unit
        return None,None

    @staticmethod
    def to_bytes(us:str,size_sample:float)->int:
        """Converts to bytes a size_sample.

        Args:
            us (str): units
            size_sample (float): size value (will be converted to int)

        Returns:
            int: size value in bytes
        """
        try:
            bytes_sample=int(size_sample)
        except (TypeError,ValueError):
            bytes_sample=None
        if us in ['bytes','by']:
            bytes_sample=int(size_sample)
        elif us == 'kb':
            bytes_sample=int(size_sample*1024)
        elif us == 'mb':
            bytes_sample=int(size_sample*1024**2)
        elif us == 'gb':
            bytes_sample=int(size_sample*1024**3)
        elif us == 'tb':
            bytes_sample=int(size_sample*1024**4)
        return bytes_sample  

    def check_operation_allowed(self,operation:str,operator:str,q_txt:str)->tuple:
        """Check operator and operation 

        Args:
            operation (str): query operation
            operator (str): query operator

        Returns:
            tuple(str,bool): (None, False) when operation is wrong
            (valid operation, True) when operation and operator are ok
            (valid operation, False) when operation ok but operator is not
        """
        if operator not in ALLOWED_OPERATORS:
            return None,False
        for valid_op, valid_op_info in ALLOWED_DICT.items():
            if operation.strip() == valid_op:
                if operator in valid_op_info['operators']:
                    if operator in ['>=','<=','<','>']:
                            return valid_op, self.check_dt_type(q_txt)        
                    return valid_op, True
                return valid_op, False
        return None,False


    def separate_queries(self,query_list:list[str]):
        """Returns a list with comma separated texts appended to a list

        Args:
            query_list (list[str]): string

        Returns:
            list: list of all texts comma separated
        """
        out_query_list=[]
        for a_query in query_list:
            a_query_list,_=self.chp.split_text(r',',a_query)
            out_query_list=out_query_list+a_query_list
        return out_query_list

    def get_queries_operations_list(self,query_list):
        """Generates operations lists from query texts

        Args:
            query_list (_type_): _description_

        Returns:
            _type_: _description_
        """
        operations_list=[]
        for a_query in query_list:
            operations_list.append(self.parse_query_operator(a_query))     
        return operations_list   

    def modify_dict_by_format(self,rec_dict:dict,is_valid:bool)->tuple:
        """Modifies the rec_dic with the correct text format, checks format

        Args:
            rec_dict (_type_): dictionary with 'operation','operator','query_text'

        Returns:
            tuple: modified rec_dict, True if format valid
        """
        if rec_dict['operation'] in ALLOWED_OPERATIONS:
            if ALLOWED_DICT[rec_dict['operation']]['format']==str(datetime):
                date_value,is_date=self.is_date_yyyymmdd_format(rec_dict['query_text'])
                time_value,is_time=self.is_time_hhmmss_format(rec_dict['query_text'])
                if is_date:
                    rec_dict['operation']=f"DATE({rec_dict['operation']})"
                    rec_dict['query_text']=date_value
                elif is_time:
                    rec_dict['operation']=f"TIME({rec_dict['operation']})"
                    rec_dict['query_text']=time_value
                else:
                    dt_value,is_valid=self.get_datetime_text(rec_dict['query_text'])
                    if is_valid and rec_dict['operator'] in ['>=','<=','<','>','==','!=']:
                        rec_dict['query_text']=dt_value
            elif ALLOWED_DICT[rec_dict['operation']]['format']==str(int):
                try:
                    val=int(rec_dict['query_text'])
                    rec_dict['query_text']=str(val)
                except (TypeError,ValueError):
                    is_valid=False
            elif ALLOWED_DICT[rec_dict['operation']]['format']==str(float):
                val,unit=self.separate_file_size_value_and_unit(rec_dict['query_text'])
                if val:
                    val=self.to_bytes(unit,val)
                    rec_dict['query_text']=str(val)
                    is_valid=True
                else:
                    is_valid=False
            elif ALLOWED_DICT[rec_dict['operation']]['format']==str(str):
                pass  
        return rec_dict,is_valid

    def check_operations_list(self,operations_list:list,and_dict:dict,or_dict:dict,sub_dict:dict):
        """Checks operations in the list for operation type

        Args:
            operations_list (list): operation list of dictionaries
                rec_dict keys:{'operation','operator''query_text'}
            and_dict (dict): and queries dictionary
            or_dict (dict): or queries dictionary
            sub_dict (dict): sub queries dictionary

        Returns:
            list(tuple): list with (type of operation, rec_dict dictionary,is valid operation)
                is_valid is evaluated only on 'op' type. Types ('op','and','or','txt','sub')
        """
        valid_operations=[]
        for rec_dict in operations_list:
            if rec_dict['operation']:
                operation,is_valid=self.check_operation_allowed(rec_dict['operation'],rec_dict['operator'],rec_dict['query_text'])
                # change datetime to iso format
                rec_dict['operation']=operation # strips
                rec_dict,is_valid=self.modify_dict_by_format(rec_dict,is_valid) 
                valid_operations.append(('op', rec_dict,is_valid))      
            else:
                content=str(rec_dict['query_text']).strip()
                if content in list(and_dict.keys()):
                    valid_operations.append(('and', rec_dict,None))
                elif content in list(or_dict.keys()):
                    valid_operations.append(('or', rec_dict,None))
                elif content in list(sub_dict.keys()):
                    valid_operations.append(('sub', rec_dict,None))
                else:
                    valid_operations.append(('txt', rec_dict,None))    
        return valid_operations

    def get_the_options_for_sub_or_and(self,op_type:str,rec_dict:dict,and_dict:dict,or_dict:dict,sub_dict:dict):
        """Returns operations in the list finding subqueries for 'and','or' and 'sub' operation types

        Args:
            op_type (str): Types ('op','and','or','txt','sub')
            rec_dict (dict): dictionary of keys:{'operation','operator''query_text'}
            and_dict (dict): and queries dictionary
            or_dict (dict): or queries dictionary
            sub_dict (dict): sub queries dictionary

        Returns:
            list(tuple): list with (type of operation, rec_dict dictionary, is valid operation)
                is_valid is evaluated for types ('and','or','sub')
        """
        if op_type in ['sub','or','and']:
            content=str(rec_dict['query_text']).strip()
            if op_type=='and':
                _operation=and_dict[content]
            elif op_type=='or':
                _operation=or_dict[content]
            else:
                _operation=sub_dict[content]
            _query_list=self.separate_queries(_operation)
            _query_list=self.remove_empty_queries(_query_list)
            _operations_list=self.get_queries_operations_list(_query_list)
            return self.check_operations_list(_operations_list,and_dict,or_dict,sub_dict)
        return None

    def check_all_operations(self,the_operations:list,and_dict:dict,or_dict:dict,sub_dict:dict):
        """_summary_

        Args:
            the_operations_list (list): list of (type of operation, rec_dict dictionary, is valid operation)
                rec_dict keys:{'operation','operator''query_text'}
            and_dict (dict): and queries dictionary
            or_dict (dict): or queries dictionary
            sub_dict (dict): sub queries dictionary

        Returns:
            tuple: msg, query, is_valid
        """
        msg=''
        query=''
        try:
            for (op_type,rec_dict,is_valid) in the_operations:
                operation=rec_dict['operation']
                if op_type=='op' and operation and is_valid==False:
                    query=str(rec_dict['operation'])+str(rec_dict['operator'])+str(rec_dict['query_text'])
                    msg=f"Error in '{query}': Can't do {rec_dict['operator']} operation for {operation}, valid operations:{ALLOWED_DICT[operation]['operators']}"
                    if not self.check_dt_type(rec_dict['query_text']):
                        query=str(rec_dict['query_text'])+' is not datetime (YYYY-MM-DD hh:mm:ss) or float format!'
                    return msg, query, False
                elif op_type=='op' and not operation and is_valid==False:
                    query=str(rec_dict['operation'])+str(rec_dict['operator'])+str(rec_dict['query_text'])
                    msg=f"Error in '{query}': is not valid input! Only {list(ALLOWED_DICT.keys())}"
                    return msg, query, False
                elif op_type in ['sub','or','and']:
                    the_op_=self.get_the_options_for_sub_or_and(op_type,rec_dict,and_dict,or_dict,sub_dict)
                    return self.check_all_operations(the_op_,and_dict,or_dict,sub_dict)
        except (TypeError,ValueError):
            return msg, query, False
        return msg, query, True    

    @staticmethod    
    def add_prefix(sql,prefix,pos):
        """adds prefix if pos>0"""
        if pos>0:
            return sql + prefix
        return sql

    @staticmethod
    def quotes(operation:str,operator:str,q_txt:str):
        if operation in ALLOWED_OPERATIONS:
            if ALLOWED_DICT[operation]['format'] in [str(int),str(float)]:
                return q_txt
            if ALLOWED_DICT[operation]['format'] in [str(datetime)]:
                return "'"+q_txt+"'"
        if operator in ['>=','<=','<','>']:
            return q_txt
        if "'" in q_txt and '"' in q_txt:
            q_txt=q_txt.replace('"','%')
        if "'" in q_txt:
            return '"'+q_txt+'"'
        
        return "'"+q_txt+"'"
    
    def get_sql_for_operation(self,operation:str,operator:str,q_txt:str,prefix:str,pos:int):
        """Gets sql construction for ['!=','<>','=','==','>=','<=','<','>','||','&&','~='] operators.

        Args:
            operation (str): operation
            operator (str): operator
            q_txt (str): query text
            prefix (str): prefix to append
            pos (int): position, if 0 then does not append the prefix

        Returns:
            str: sql query
        """
        sql=""
        sql=self.add_prefix(sql,prefix,pos)
        if operator == "=":
            sql=sql+ f"{operation} LIKE {self.quotes(operation,operator,q_txt.replace('*','%'))}"
        elif operator == "~=":    
            sql=sql+ f"UPPER({operation}) LIKE {self.quotes(operation,operator,q_txt.replace('*','%').upper())}"
        elif operator == '==':
            sql=sql+ f"{operation} = {self.quotes(operation,operator,q_txt)}"
        elif operator == '!=':
            sql=sql+ f"{operation} NOT LIKE {self.quotes(operation,operator,q_txt.replace('*','%'))}"
        elif operator == '<>':
            sql=sql+ f"UPPER({operation}) NOT LIKE {self.quotes(operation,operator,q_txt.replace('*','%').upper())}"
        elif operator in ['>=','<=','<','>']:
            sql=sql+ f"{operation} {operator} {self.quotes(operation,operator,q_txt)}"
        elif operator in ['&&','||']:
            sql=sql+ f"{operation} {' OR ' if operator=='||' else ' AND '} {self.quotes(operation,operator,q_txt)}"
        return sql

    def get_where_sql_of_operations(self,the_operations:list,and_dict:dict,or_dict:dict,sub_dict:dict,sql:str=None):
        """Generates SQL string for where using The operations list for all operation types

        Args:
            the_operations_list (list): list of (type of operation, rec_dict dictionary, is valid operation)
                rec_dict keys:{'operation','operator''query_text'}
            and_dict (dict): and queries dictionary
            or_dict (dict): or queries dictionary
            sub_dict (dict): sub queries dictionary
            sql (str, optional): Sql to append. Defaults to None.

        Returns:
            str: SQL Query for operations list
        """
        if not sql:
            sql=""
        for iii,(op_type,rec_dict,is_valid) in enumerate(the_operations):
            operation=str(rec_dict['operation'])
            operator=str(rec_dict['operator'])
            q_txt=str(rec_dict['query_text'])
            if op_type=='op'and operation and is_valid:
                if q_txt.strip() in list(sub_dict.keys()):
                    the_op_=self.get_the_options_for_sub_or_and('sub',rec_dict,and_dict,or_dict,sub_dict)
                    mod_the_op_=[]
                    for (_, sub_rec_dict,_) in the_op_:
                        sub_rec_dict['operation']=operation
                        sub_rec_dict['operator']=operator
                        mod_the_op_.append((op_type, sub_rec_dict,True))
                    sql=sql+' OR ('+self.get_where_sql_of_operations(mod_the_op_,and_dict,or_dict,sub_dict,None)+')'
                else:
                    sql=sql+self.get_sql_for_operation(operation,operator,q_txt,' OR ',iii)
            elif op_type=='txt':
                if q_txt.strip() in list(sub_dict.keys()):
                    the_op_=self.get_the_options_for_sub_or_and('sub',rec_dict,and_dict,or_dict,sub_dict)
                    sql=sql+' OR ('+self.get_where_sql_of_operations(the_op_,and_dict,or_dict,sub_dict,None)+')'
                else:
                    sql=sql+self.get_sql_for_operation('filename','~=',q_txt,' OR ',iii)
            elif op_type =='or': #in ['sub','or']:
                the_op_=self.get_the_options_for_sub_or_and(op_type,rec_dict,and_dict,or_dict,sub_dict)
                opt_sql=self.get_where_sql_of_operations(the_op_,and_dict,or_dict,sub_dict,None)
                sql=sql+' ('+opt_sql+')'
            elif op_type=='and':
                the_op_=self.get_the_options_for_sub_or_and(op_type,rec_dict,and_dict,or_dict,sub_dict)
                opt_sql=self.get_where_sql_of_operations(the_op_,and_dict,or_dict,sub_dict,None)
                sql=sql+' ('+opt_sql.replace(' OR ',' AND ')+')'
            else:    
                pass 
        return sql
    
    def get_sql_from_text_input(self,text_input:str)->tuple:
        """Returns the SQL code of a text input

        Args:
            text_input (str): _description_

        Returns:
            tuple: _description_
        """
        all_query_list=[]
        msg=''
        sql=None
        if self.chp.check_parenthesees_in_one_format(text_input):
            # Look for keywords
            msg='Parenthesys Check ok!'
            main_query_list,_=self.chp.format_which_inside_parenthesees(text_input,r"\[",r"\]")
            if len(main_query_list)==0 and text_input.strip() != '':
                main_query_list=[text_input]
            #Get sub queries
            main_query_list,sub_query_dict=self.get_sub_queries(main_query_list,None)
            # Separate main queries            
            all_query_list=self.separate_queries(main_query_list)
            #Remove empty
            all_query_list=self.remove_empty_queries(all_query_list)
            #Deal with and and or
            #print(sub_query_dict)
            all_query_list, and_dict, or_dict=self.get_and_or_dictionaries(all_query_list,None,None)
            operations_list=self.get_queries_operations_list(all_query_list)
            the_operations=self.check_operations_list(operations_list,and_dict,or_dict,sub_query_dict)
            msg,query,is_valid=self.check_all_operations(the_operations,and_dict,or_dict,sub_query_dict)
            # print(is_valid,msg)
            if is_valid:
                sql=self.get_where_sql_of_operations(the_operations,and_dict,or_dict,sub_query_dict,None)
                return sql,msg,is_valid
            if query != '':
                msg=msg+"\n"+query
            return sql,msg,is_valid
        return sql,msg,False
    
    

#  [filename=*.py , filepath=*py*, filename=*.py && filepath=*on* ]
#  [filename=*.py, filepath=(path1,path2), ...]
# text_input='[filename=*.py, filepath==*!=py*, filename=*.py && filepath=*on>*, filepath=(path1,path2), filename=*.py || filepath=(path3!+path2), (text,text1), text2 ]'
if __name__ == "__main__":
    from class_autocomplete_input import *
    from rich import print
    import rich.text  
    AC = AutocompletePathFile(
        "return string (ENTER), Autofill path/file (TAB), Cancel (ESC) Paste (CTRL+V)\nPlease type path: ",
        APP_PATH,
        False,
        verbose=False,
        inquire=False,
    )
    SQL_SG=SQLSearchGenerator()
        
    def test_sql():
        # You can use key_pressed() inside a while loop:
        text_input=''
        pos=0
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            sql,msg,is_valid=SQL_SG.get_sql_from_text_input(text_input)
            print("Test", pos)
            print("Message:",msg)
            print("Input Valid:",is_valid)
            print("SQL:",sql)
            if AC.options != '':
                print(AC.options)
            pretxt="Input Text:"
            print(rich.text.Text(AC.highlight_cursor(pretxt+text_input, len(pretxt)+pos)),end='')
            (key_handle,is_special)=AC.wait_key_press()
            if not is_special:
                text_input=AC.insert_char_at_pos(text_input,key_handle,pos)
                pos += 1
            if key_handle == 'backspace':
                if pos>0:
                    text_input=AC.remove_char_at_pos(text_input,pos)
                    pos += -1
            if key_handle == 'delete':
                if pos<len(text_input):
                    text_input=AC.remove_char_at_pos(text_input,pos+1)
            if key_handle == 'enter':
                return sql,msg,is_valid
            if key_handle == 'arrowleft':
                pos += -1
            if key_handle == 'arrowright':
                pos += 1
            if key_handle == 'home':
                pos = 0
            if key_handle == 'end':
                pos = len(text_input)
            if key_handle == 'tab':
                AC.options = ""
                auto=AC.autocomplete_from_list(text_input[:pos],ALLOWED_OPERATIONS)
                text_input=text_input[:pos]+auto+text_input[pos:]
                pos=len(text_input[:pos]+auto)
            if key_handle == 'esc':
                return '','User Cancel',False
            if pos<0:
                pos=0
            elif pos>=len(text_input):
                pos=len(text_input)
            

    print('Result:',test_sql())
    # text_input='text2'
    # print(f'[yellow]initial query:{str(text_input)}')  
    # print(get_sql_from_text_input(text_input))





            
