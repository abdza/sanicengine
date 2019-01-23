# -*- coding: utf-8 -*-
"""User models."""
import datetime

from sanicengine.database import ModelBase, dbsession, reference_col, executedb
from sqlalchemy import column, Column, ForeignKey, Integer, String, Text, Boolean, DateTime, Date, Table, MetaData, select, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import text
from sanicengine.template import render_string
from sanicengine.users.models import ModuleRole, User
from sanicengine.pages.models import Page
from sanicengine.fileLinks.models import FileLink
from sanicengine import settings
from openpyxl import load_workbook
import json
import math
import os
import time

class Tracker(ModelBase):
    __tablename__ = 'trackers'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100))
    module = Column(String(100),default='portal')
    default_new_transition = Column(String(100))
    list_fields = Column(Text)
    search_fields = Column(Text)
    filter_fields = Column(Text)
    excel_fields = Column(Text)
    detail_fields = Column(Text)
    published = Column(Boolean(),default=False)
    pagelimit = Column(Integer,default=10)
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))
    publish_date = Column(Date(),nullable=True)
    expire_date = Column(Date(),nullable=True)
    data_table_name = Column(String(200))
    update_table_name = Column(String(200))

    __table_args__ = (
        UniqueConstraint(module, slug, name='tracker_module_slug_uidx'),
    )

    def __repr__(self):
        return self.title

    def load(slug,module=None):
        tracker = dbsession.query(Tracker).filter_by(slug=slug)
        if module:
            tracker = tracker.filter_by(module=module)
        return tracker.first()

    @property
    def is_published(self):
        if not self.published:
            return False
        else:
            toret = True
            curdate = datetime.date.today()
            if self.publish_date and self.publish_date>curdate:
                toret = False
            if self.expire_date and self.expire_date<curdate:
                toret = False
            return toret

    def list_fields_list(self):
        rfields = []
        if self.list_fields:
            pfields = self.list_fields.split(',')
            for pfield in pfields:
                rfield = dbsession.query(TrackerField).filter_by(tracker=self,name=pfield.strip()).first()
                if rfield:
                    rfields.append(rfield)
        return rfields

    def display_fields_list(self,record):
        curstatus = self.status(record)
        if curstatus:
            if curstatus.display_fields:
                return self.fields_from_list(curstatus.display_fields)
            elif self.detail_fields:
                return self.fields_from_list(self.detail_fields)
        return []

    def fields_from_list(self,field_list=None):
        rfields = []
        if field_list:
            pfields = field_list.split(',')
            rfields = []
            for pfield in pfields:
                rfield = dbsession.query(TrackerField).filter_by(tracker=self,name=pfield.strip()).first()
                if rfield:
                    rfields.append(rfield)
        return rfields

    @property
    def data_table(self):
        if self.data_table_name:
            return self.data_table_name
        else:
            return "trak_" + self.module + "_" + self.slug + "_data"

    @property
    def update_table(self):
        if self.update_table_name:
            return self.update_table_name
        else:
            return "trak_" + self.module + "_" + self.slug + "_updates"

    @property
    def pages(self):
        return dbsession.query(Page).filter_by(module=self.module).all()

    def field(self, name):
        field = dbsession.query(TrackerField).filter_by(tracker=self,name=name.strip()).first()
        return field

    def updatedb(self):
        query = """
            do $$
            begin
            if (select not exists(select  1 from information_schema.sequences where sequence_schema = 'public' and sequence_name = '""" + self.data_table + """_id_seq'))
            then
                create sequence public.""" + self.data_table + """_id_seq
                increment 1
                minvalue 1
                maxvalue 9223372036854775807
                start 1
                cache 1;
            end if;
            if (select not exists(select  1 from information_schema.tables where table_schema = 'public' and table_name = '""" + self.data_table + """'))
            then
                create table public.""" + self.data_table + """(
                    id integer not null default nextval('""" + self.data_table + """_id_seq'::regclass),
                    record_status character varying(50) ,
                    batch_no integer
                );
            end if;
            if (select not exists(select  1 from information_schema.sequences where sequence_schema = 'public' and sequence_name = '""" + self.update_table + """_id_seq'))
            then
                create sequence public.""" + self.update_table + """_id_seq
                increment 1
                minvalue 1
                maxvalue 9223372036854775807
                start 1
                cache 1;
            end if;
            if (select not exists(select  1 from information_schema.tables where table_schema = 'public' and table_name = '""" + self.update_table + """'))
            then
                create table public.""" + self.update_table + """(
                    id integer not null default nextval('""" + self.update_table + """_id_seq'::regclass),
                    record_id integer,
                    user_id integer,
                    record_status character varying(50),
                    update_date timestamp,
                    description text
                );
            end if;
            end$$;
        """
        dbsession.execute(query)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
        for field in self.fields:
            field.updatedb()

    def first(self, query):
        return executedb("select * from " + self.data_table + " where " + query).first()

    def saverecord(self, record, request=None):
        curuser = None
        data = None
        if request:
            if 'user_id' in request['session']:
                curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
        if 'id' in record:
            query = """update """ + self.data_table + """ set """ + ",".join([ formfield + "=" + self.field(formfield).sqlvalue(record[formfield]) for formfield in record.keys()  ]) + """ where id=""" + str(record['id']) + " returning *"
        else:
            query = """
                insert into """ + self.data_table + """ ( """ + ",".join(record.keys()) + """) values 
                (""" + ",".join([ self.field(formfield).sqlvalue(record[formfield]) for formfield in record.keys()  ]) + """) returning *
            """
        try:
            data = dbsession.execute(query).fetchone()
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
        return data

    def addrecord(self, form, request):
        curuser = None
        data = None
        if 'user_id' in request['session']:
            curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
        if 'transition_id' in form:
            transition = dbsession.query(TrackerTransition).get(form['transition_id'][0])
            del(form['transition_id'])
            if transition:
                if transition.next_status:
                    form['record_status'] = [transition.next_status.name,]
                for field in transition.edit_fields_list():
                    if field.default and field.name in form and form[field.name][0]=='systemdefault':
                        output=None
                        ldict = locals()
                        exec(field.default,globals(),ldict)
                        output=ldict['output']
                        form[field.name][0]=output
                    elif field.field_type in ['file','picture','video']:
                        if request.files.get(field.name) and request.files.get(field.name).name:
                            filelink=FileLink()
                            dfile = request.files.get(field.name)
                            ext = dfile.type.split('/')[1]
                            if not os.path.exists(os.path.join('upload',self.module)):
                                os.makedirs(os.path.join('upload',self.module))
                            outfilename = str(int(time.time())) + dfile.name
                            dst = os.path.join('upload',self.module,outfilename)
                            try:
                                # extract starting byte from Content-Range header string
                                range_str = request.headers['Content-Range']
                                start_bytes = int(range_str.split(' ')[1].split('-')[0])
                                with open(dst, 'ab') as f:
                                    f.seek(start_bytes)
                                    f.write(dfile.body)
                            except KeyError:
                                with open(dst, 'wb') as f:
                                    f.write(dfile.body)
                            filelink.filename = dfile.name
                            filelink.filepath = dst
                            filelink.module = self.module
                            filelink.slug = outfilename.replace(' ','_').lower()
                            filelink.title = dfile.name
                            filelink.published = True
                            filelink.require_login = False
                            dbsession.add(filelink)
                            dbsession.commit()
                            form[field.name]=[filelink.id,]
        fieldnames = list(form.keys())
        query = """
            insert into """ + self.data_table + """ ( """ + ",".join(fieldnames) + """) values 
            (""" + ",".join([ self.field(formfield).sqlvalue(form[formfield][0]) for formfield in fieldnames  ]) + """) returning *
        """
        try:
            data = dbsession.execute(query).fetchone()
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
        desc = ''
        if curuser:
            desc = 'Updated by ' + curuser.name
        else:
            desc = 'Updated by anonymous'

        try:
            query = """
                insert into """ + self.update_table + """ (record_id,user_id,record_status,update_date,description) values 
                ( """ + str(data['id']) + "," + (str(curuser.id) + "," if curuser else 'null,') + "'" + data['record_status'] + "',now(),'" + desc + "') "
            dbsession.execute(query)
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()

        return data

    def editrecord(self, form, request, id=None):
        curuser = None
        transition = None
        if 'user_id' in request['session']:
            curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
        if 'transition_id' in form:
            transition = dbsession.query(TrackerTransition).get(form['transition_id'][0])
            if transition and transition.next_status:
                form['record_status'] = [transition.next_status.name,]
            del(form['transition_id'])
        oldrecord = None
        if id:
            oldrecord = self.records(id,curuser=curuser,request=request)
        elif 'id' in form:
            oldrecord = self.records(form['id'][0],curuser=curuser,request=request)
            del(form['id'])
        data = None
        if transition:
            if form['record_status'][0].lower()=='delete':
                if oldrecord:
                    request['session']['flashmessage']="Deleted " + self.title + " " + str(oldrecord['id'])
                    try:
                        dbsession.execute("delete from " + self.update_table + " where record_id=" + str(oldrecord['id']))
                    except Exception as inst:
                        dbsession.rollback()
                    try:
                        dbsession.execute("delete from " + self.data_table + " where id=" + str(oldrecord['id']))
                    except Exception as inst:
                        dbsession.rollback()
                    return None
            else:
                for field in transition.edit_fields_list():
                    if field.default and field.name in form and form[field.name][0]=='systemdefault':
                        output=None
                        ldict = locals()
                        try:
                            exec(field.default,globals(),ldict)
                            output=ldict['output']
                            form[field.name][0]=output
                        except Exception as inst:
                            print("Error exec:" + str(field.default))
                    elif field.field_type == 'boolean':
                        if field.name not in form:
                            form[field.name]=[0,]
                    elif field.field_type in ['file','picture','video']:
                        if request.files.get(field.name) and request.files.get(field.name).name:
                            filelink=FileLink()
                            dfile = request.files.get(field.name)
                            ext = dfile.type.split('/')[1]
                            if not os.path.exists(os.path.join('upload',self.module)):
                                os.makedirs(os.path.join('upload',self.module))
                            outfilename = str(int(time.time())) + dfile.name
                            dst = os.path.join('upload',self.module,outfilename)
                            try:
                                # extract starting byte from Content-Range header string
                                range_str = request.headers['Content-Range']
                                start_bytes = int(range_str.split(' ')[1].split('-')[0])
                                with open(dst, 'ab') as f:
                                    f.seek(start_bytes)
                                    f.write(dfile.body)
                            except KeyError:
                                with open(dst, 'wb') as f:
                                    f.write(dfile.body)
                            filelink.filename = dfile.name
                            filelink.filepath = dst
                            filelink.module = self.module
                            filelink.slug = outfilename.replace(' ','_').lower()
                            filelink.title = dfile.name
                            filelink.published = True
                            filelink.require_login = False
                            dbsession.add(filelink)
                            dbsession.commit()
                            form[field.name]=[filelink.id,]
                fieldnames = list(form.keys())
                if oldrecord:
                    query = """update """ + self.data_table + """ set """ + ",".join([ formfield + "=" + self.field(formfield).sqlvalue(form[formfield][0]) for formfield in fieldnames  ]) + """ where id=""" + str(oldrecord['id']) + " returning *"
                try:
                    data = dbsession.execute(query).fetchone()
                    dbsession.commit()
                except Exception as inst:
                    print("Error query:" + str(query))
                    dbsession.rollback()
                txtdesc = []
                if data:
                    for okey,oval in enumerate(oldrecord):
                        if oval!=data[okey]:
                            dfield = dbsession.query(TrackerField).filter_by(name=oldrecord.keys()[okey]).first()
                            if dfield:
                                txtdesc.append('Updated ' + dfield.label + ' from ' + str(oval) + ' to ' + str(data[okey]))
                            else:
                                print("not found")
                    desc = '<br>'.join(txtdesc)

                    query = """
                        insert into """ + self.update_table + """ (record_id,user_id,record_status,update_date,description) values 
                        ( """ + str(data['id']) + "," + (str(curuser.id) + "," if curuser else 'null,') + "'" + data['record_status'] + "',now(),'" + desc + "') "
                    try:
                        dbsession.execute(query)
                        dbsession.commit()
                    except Exception as inst:
                        print("Error query:" + str(query))
                        dbsession.rollback()

        return data

    def pagelinks(self,curuser=None,request=None,cleared=False):
        # plo : page list offset
        # pll : page list limit
        pageamount = 0
        try:
            recordamount = dbsession.execute("select count(*) as num from " + self.data_table + self.queryrules(curuser=curuser, request=request)).first()['num']
            pageamount = int(math.ceil(recordamount/(self.pagelimit if self.pagelimit else 10)))
        except Exception as inst:
            print("Exception getting record amount:" + str(inst))
            dbsession.rollback()
        links = []
        curoffset = 0
        if request:
            curoffset = int(request.args['plo'][0]) if 'plo' in request.args else 0
        curindex = 0
        for x in range(0,pageamount):
            nextoffset=((x+1)*(self.pagelimit if self.pagelimit else 10) if x+1<pageamount else None)
            prevoffset=((x-1)*(self.pagelimit if self.pagelimit else 10) if x else None)
            offset=x*(self.pagelimit if self.pagelimit else 10)
            params = {'slug':self.slug,'pll':(self.pagelimit if self.pagelimit else 10)}
            if 'plq' in request.args:
                params.update({'plq':request.args['plq'][0]})
            if self.filter_fields:
                ffields = self.fields_from_list(self.filter_fields)
                for ff in ffields:
                    pname = 'filter_' + ff.name
                    if pname in request.args:
                        params.update({pname:request.args[pname][0]})
            params.update({'plo':offset})
            url=request.app.url_for('trackers.viewlist',module=self.module,**params)
            params.update({'plo':prevoffset})
            prevlink = (request.app.url_for('trackers.viewlist',module=self.module,**params)) if prevoffset else None
            params.update({'plo':nextoffset})
            nextlink = (request.app.url_for('trackers.viewlist',module=self.module,**params)) if nextoffset else None
            thislink = { 'url':url,'nextlink':nextlink,'prevlink':prevlink }
            if curoffset==x*(self.pagelimit if self.pagelimit else 10):
                curindex = x
            links.append(thislink)
        return curindex,links

    def queryrules(self,curuser=None,request=None,cleared=False):
        rules = ' where 1=1 '
        if request and 'plq' in request.args: # page list query exists
            if self.search_fields and len(request.args['plq'][0]):
                sfields = self.fields_from_list(self.search_fields)
                sqs = []
                for sfield in sfields:
                    sqs.append(sfield.queryvalue(request.args['plq'][0]))
                rules += ' and (' + ' or '.join(sqs) + ')'

        if self.filter_fields:
            ffields = self.fields_from_list(self.filter_fields)
            fqs = []
            for ffield in ffields:
                if 'filter_' + ffield.name in request.args and request.args['filter_'+ffield.name][0]!='plall':
                    fqs.append(ffield.queryvalue(request.args['filter_'+ffield.name][0],equals=True))
            if len(fqs):
                rules += ' and (' + ' and '.join(fqs) + ')'

        if not cleared:
            rrules = self.rolesrule(curuser,request)
            if rrules:
                rules += ' and (' + rrules + ') '
        return rules

    def records(self,id=None,curuser=None,request=None,cleared=False,offset=None,limit=None):
        results = []
        if id:
            if cleared:
                sqltext = text("select * from " + self.data_table +  " where id=:id")
            else:
                sqltext = text("select * from " + self.data_table +  " where id=:id and (" + self.rolesrule(curuser,request) + ")")
            sqltext = sqltext.bindparams(id=id)
        else:
            limitstr = ''
            offsetstr = ''
            if limit:
                limitstr = ' limit ' + str(limit)
            if offset:
                offsetstr = ' offset ' + str(offset)
            sqltext = text("select * from " + self.data_table + self.queryrules(curuser=curuser,request=request,cleared=cleared) + limitstr + offsetstr)
        try:
            results = dbsession.execute(sqltext)
        except Exception as inst:
            dbsession.rollback()
        if id:
            drows = None
            for row in results:
                drows = row
            results = drows
        return results

    def rolesrule(self,curuser,request):
        if self.userroles(curuser,request=request):
            rolesrule = '1=1'
        else:
            queryroles = dbsession.query(TrackerRole).filter_by(tracker=self,role_type='query').all()
            rolesrule = '1=0'
            rulestext = [ render_string(request,role.compare) for role in queryroles ]
            if len(rulestext):
                trolesrule = ' or '.join(rulestext)
                if len(trolesrule):
                    rolesrule = trolesrule
        return rolesrule

    def status(self,record):
        if record and 'record_status' in record and record['record_status']:
            status = dbsession.query(TrackerStatus).filter_by(tracker=self,name=record['record_status']).first()
            if status:
                return status
        return None

    def userroles(self,curuser,record=None,request=None):
        croles = []
        for role in self.roles:
            if role.role_type=='module':
                usermoduleroles = dbsession.query(ModuleRole).filter(ModuleRole.module==self.module,ModuleRole.user==curuser,ModuleRole.role==role.name).all()
                if len(usermoduleroles):
                    croles.append(role)
            elif record:
                rolesrule = render_string(request,role.compare)
                sqltext = "select id from " + self.data_table + " where id=" + str(record['id']) + " and " + rolesrule
                try:
                    results = dbsession.execute(sqltext)
                    if results:
                        for row in results:
                            croles.append(role)
                except Exception as inst:
                    print("Error running query:" + str(inst))
                    dbsession.rollback()
        return croles

    def activetransitions(self,record,curuser,request):
        status = self.status(record)
        roles = self.userroles(curuser,record,request=request)
        atransitions = []
        if status:
            transitions = dbsession.query(TrackerTransition).filter(TrackerTransition.prev_status==status,TrackerTransition.tracker==self).all()
            if len(transitions) and len(roles):
                for t in transitions:
                    for r in roles:
                        if r in t.roles:
                            atransitions.append(t)
        return atransitions

    def recordupdates(self,record,curuser):
        updates = []
        if record:
            try:
                updates = dbsession.execute("select * from " + self.update_table + " where record_id=" + str(record['id']) + " order by update_date desc")
            except Exception as inst:
                print("Error updating record:" + str(inst))
                dbsession.rollback()
        return updates


class TrackerField(ModelBase):
    __tablename__ = 'tracker_fields'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    label = Column(String(50))
    field_type = Column(String(20))
    widget = Column(String(20))
    obj_table = Column(String(50))
    obj_field = Column(String(100))
    default = Column(Text())
    options = Column(Text())
    foreignfields = []

    tracker_id = reference_col('trackers')
    tracker = relationship('Tracker',backref='fields')

    def __repr__(self):
        return self.label

    def load_foreign_fields(self):
        if self.field_type=='hasMany' and self.obj_table and self.obj_field:
            self.foreignfields = []
            tt = self.obj_table.split('.')
            dtracker = dbsession.query(Tracker).filter_by(module=tt[0],slug=tt[1]).first()
            if dtracker:
                for f in self.obj_field.split(','):
                    ddm = dbsession.query(TrackerField).filter_by(tracker=dtracker,name=f.strip()).first()
                    if ddm:
                        self.foreignfields.append(ddm)

    def obj_fields(self):
        if self.obj_field:
            return self.obj_field.split(',')

    def main_obj_field(self):
        if self.obj_field:
            return self.obj_fields()[0]

    def filter_options(self):
        values = []
        try:
            if self.field_type == 'object' and self.obj_table and self.obj_field:
                cobj_field = self.main_obj_field()
                values = dbsession.execute("select distinct cur." + self.name + " as val, ref." + cobj_field + " as label from " + self.tracker.data_table + " cur, " + self.obj_table + " ref where ref.id=cur." + self.name + " order by " + cobj_field)
            elif self.field_type == 'user':
                values = dbsession.execute("select distinct cur." + self.name + " as val, ref.name as label from " + self.tracker.data_table + " cur, users ref where ref.id=cur." + self.name + " order by " + self.name)
            else:
                values = dbsession.execute("select distinct " + self.name + " as val from " + self.tracker.data_table + " order by " + self.name)
        except Exception as inst:
            print("Error getting filter:" + str(inst))
            dbsession.rollback()
        return values

    def disp_options(self):
        if self.options:
            output=None
            try:
                ldict = locals()
                exec(field.options,globals(),ldict)
                output=ldict['output']
            except:
                output=self.options.split(',')
            return output
        else:
            return None

    def disp_value(self, value, request=None):
        if value:
            if self.field_type=='object':
                sqlq = "select " + self.main_obj_field() + " from " + self.obj_table + " where id=" + str(value)
                try:
                    result = dbsession.execute(sqlq)
                    for r in result:
                        return r[0]
                except Exception as inst:
                    print("Error running query:" + str(inst))
                    dbsession.rollback()
            elif self.field_type=='treenode':
                sqlq = "select string_agg(cnode.title,'->' order by cnode.lft) from tree_nodes cnode,(select id,lft,rgt,tree_id from tree_nodes where id=" + str(value) + ") nleaf where cnode.lft<=nleaf.lft and cnode.rgt>=nleaf.rgt and cnode.tree_id=nleaf.tree_id group by nleaf.lft,nleaf.rgt,nleaf.id,nleaf.tree_id"
                try:
                    result = dbsession.execute(sqlq)
                    for r in result:
                        return r[0]
                except Exception as inst:
                    print("Error running query:" + str(inst))
                    dbsession.rollback()
            elif self.field_type=='user':
                sqlq = "select name from users where id=" + str(value)
                try:
                    result = dbsession.execute(sqlq)
                    for r in result:
                        return r[0]
                except Exception as inst:
                    print("Error running query:" + str(inst))
                    dbsession.rollback()
            elif self.field_type == 'picture' or self.widget== 'picture':
                filelink = dbsession.query(FileLink).get(value)
                if filelink:
                    url=request.app.url_for('fileLinks.download',module=filelink.module,slug=filelink.slug)
                    value = "<img src='" + url + "'>"
            elif self.field_type == 'video' or self.widget== 'video':
                filelink = dbsession.query(FileLink).get(value)
                if filelink:
                    url=request.app.url_for('fileLinks.download',module=filelink.module,slug=filelink.slug)
                    value = "<video controls><source src='" + url + "'></video>"
            elif self.field_type in ['location','map']:
                mlat = value.split(',')
                try:
                    if len(mlat)>1 and settings.GOOGLE_MAPS_API:
                        mapstr = "<div id='" + self.name + "_div' style='height: 400px;'></div>"
                        mapstr += "<script>var " + self.name + "_map," + self.name + "_marker; "
                        mapstr += "function init_" + self.name + "_map(){ " + self.name + "_map = new google.maps.Map(document.getElementById('" + self.name + "_div'), { center: {lat: " + mlat[0] + ",lng:" + mlat[1] + "}, zoom: 13 }); " + self.name + "_marker = new google.maps.Marker({ position: {lat:" + mlat[0] + ",lng:" + mlat[1] + " }, map: " + self.name + "_map }); }</script>"
                        return mapstr
                    else:
                        return 'Map failed to render for location: ' + value
                except:
                    return 'Map failed to render for location: ' + value
            
        if self.field_type=='boolean':
            if not value:
                value = 'False'
            else:
                value = 'True'
        return value

    def queryvalue(self, value,equals=False):
        if self.field_type in ['string','text','location','map']:
            if equals:
                return self.name + " = '" + str(value) + "'"
            else:
                return self.name + " ilike '%" + str(value) + "%'"
        elif self.field_type in ['integer','number','object','treenode','user','file','picture','video']:
            return self.name + "=" + str(value)
        elif self.field_type in ['date','datetime']:
            return self.name + "='" + str(value) + "'"
        return "1=1"

    def sqlvalue(self, value):
        if value:
            if self.field_type in ['string','text','date','datetime','location','map']:
                return "'" + str(value).replace("'","''") + "'"
            elif self.field_type in ['integer','number','object','treenode','user','file','picture','video']:
                return str(value)
            elif self.field_type=='boolean':
                if value:
                    return 'true'
                else:
                    return 'false'
        else:
            return "null"
        return ''

    def dbcolumn(self):
        return column(self.name)

    def db_field_type(self):
        if self.field_type=='string':
            return 'character varying(200)'
        elif self.field_type in ['location','map']:
            return 'character varying(200)'
        elif self.field_type=='text':
            return 'text'
        elif self.field_type=='integer':
            return 'integer'
        elif self.field_type=='object':
            return 'integer'
        elif self.field_type=='treenode':
            return 'integer'
        elif self.field_type=='user':
            return 'integer'
        elif self.field_type=='belongsTo':
            return 'integer'
        elif self.field_type=='file':
            return 'integer'
        elif self.field_type=='picture':
            return 'integer'
        elif self.field_type=='video':
            return 'integer'
        elif self.field_type=='number':
            return 'double precision'
        elif self.field_type=='date':
            return 'date'
        elif self.field_type=='datetime':
            return 'timestamp'
        elif self.field_type=='boolean':
            return 'boolean'

    def updatedb(self):
        if not self.field_type=='hasMany':
            query = """
                do $$
                begin 
                    IF not EXISTS (SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema='public' and table_name='""" + self.tracker.data_table + """' and column_name='""" + self.name + """') THEN
                            alter table public.""" + self.tracker.data_table + """ add column """ + self.name + " " + self.db_field_type() + """ null ;
                    end if;
                end$$;
            """
            try:
                dbsession.execute(query)
                dbsession.commit()
            except Exception as inst:
                print("Error running updating db:" + str(inst))
                dbsession.rollback()

class TrackerRole(ModelBase):
    __tablename__ = 'tracker_roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    role_type = Column(String(10))
    compare = Column(Text,nullable=True)

    tracker_id = reference_col('trackers')
    tracker = relationship('Tracker',backref='roles')

    def __repr__(self):
        return self.name

class TrackerDataUpdate(ModelBase):
    __tablename__ = 'tracker_data_update'
    id = Column(Integer, primary_key=True)
    status = Column(String(50))
    created_date = Column(DateTime)
    filename = Column(String(200))
    data_params = Column(Text,nullable=True)

    tracker_id = reference_col('trackers')
    tracker = relationship('Tracker',backref='dataupdates')

    def __repr__(self):
        return self.tracker.title + ' ' + str(self.created_date)

    async def run(self):
        wb = load_workbook(filename = self.filename)
        ws = wb.active
        print('data:' + str(self.data_params))
        datas = json.loads(self.data_params)
        fields = []
        optype = 'insert'
        searchfield = []
        for field in self.tracker.fields:
            if field.name != 'id' and datas[field.name + '_column'][0]!='ignore':
                fields.append(field)
            if field.name + '_update' in datas:
                optype = 'update'
                searchfield.append(field)
        rows = []
        headerend = 1
        if optype == 'insert':
            recstatusq = ''
            newtransition = None
            if 'record_status' not in fields:
                recstatusq = ',record_status'
                newtransition = dbsession.query(TrackerTransition).filter(TrackerTransition.tracker==self.tracker,TrackerTransition.name==self.tracker.default_new_transition).first()
            query = 'insert into ' + self.tracker.data_table + ' (' + ','.join([ f.name for f in fields ]) + ',batch_no' + recstatusq + ') values '
            for i,row in enumerate(ws.rows):
                if i>=headerend:
                    cellrows = [ws[datas[f.name + '_column'][0] + str(i+1)] if datas[f.name + '_column'][0]!='custom' else datas[f.name + '_custom'][0] for f in fields]
                    drowdata = [ f.value if type(f) is not str else f for f in cellrows ]
                    sqlrowdata = [ f.sqlvalue(drowdata[dd]) for dd,f in enumerate(fields) ]
                    drow = '('
                    drow = drow + ','.join(sqlrowdata)
                    drow = drow + ',' + str(self.id)
                    if 'record_status' not in fields and newtransition and newtransition.next_status:
                        drow = drow + ",'" + newtransition.next_status.name + "'"
                    drow = drow + ')'
                    rows.append(drow)
            query = query + ','.join(rows)
            try:
                dbsession.execute(query)
                dbsession.commit()
                self.status = 'Uploaded ' + str(len(rows)) + ' rows'
                dbsession.add(self)
                dbsession.commit()
            except Exception as inst:
                print("Error inserting data:" + str(inst))
                dbsession.rollback()
        else:
            allresults = []
            for i,row in enumerate(ws.rows):
                if i>headerend:
                    fieldupdates = []
                    for f in searchfield:
                        cellrow = ws[datas[f.name + '_column'][0] + str(i+1)]
                        fieldupdates.append( f.name + '=' + f.sqlvalue(cellrow.value) )
                    queryrow = ' where ' + 'and'.join(fieldupdates)

                    sqltext = text("select id from " + self.tracker.data_table + queryrow)
                    try:
                        result = dbsession.execute(sqltext)
                        gotdata = False
                        for r in result:
                            gotdata = True
                    except Exception as inst:
                        print("Error running query:" + str(inst))
                        dbsession.rollback()
                    
                    if gotdata:
                        query = 'update ' + self.tracker.data_table + ' set ' 
                        fieldinfos = []
                        for f in fields:
                            if not f in searchfield:
                                if datas[f.name + '_column'][0]!='custom':
                                    cellrow = ws[datas[f.name + '_column'][0] + str(i+1)]
                                    fieldinfos.append( f.name + '=' + f.sqlvalue(cellrow.value) )
                                else:
                                    cellrow = datas[f.name + '_custom'][0]
                                    fieldinfos.append( f.name + '=' + f.sqlvalue(cellrow) )
                        query += ','.join(fieldinfos) + queryrow + ' returning *'
                        try:
                            result = dbsession.execute(query)
                        except Exception as inst:
                            print("Error runing query:" + str(inst))
                            dbsession.rollback()
                    else:
                        celldatas = {}
                        for f in fields:
                            if datas[f.name + '_column'][0]!='custom':
                                celldatas[f.name] = ws[datas[f.name + '_column'][0] + str(i+1)].value
                            else:
                                celldatas[f.name] = datas[f.name + '_custom'][0]
                        query = 'insert into ' + self.tracker.data_table + ' (' + ','.join([ f.name for f in fields ]) + ',batch_no) values (' + ','.join([ f.sqlvalue(celldatas[f.name]) for f in fields ]) + ',' + str(self.id) + ')'
                        query += ' returning *'
                        result = dbsession.execute(query)
                    try:
                        dbsession.commit()
                        allresults.append('Uploaded ' + str(result.first()))
                    except Exception as inst:
                        dbsession.rollback()
            try:
                self.status = 'Updated ' + str(len(allresults)) + ' rows'
                dbsession.add(self)
                dbsession.commit()
            except Exception as inst:
                dbsession.rollback()
        return True

class TrackerStatus(ModelBase):
    __tablename__ = 'tracker_statuses'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    display_fields = Column(Text)

    tracker_id = reference_col('trackers')
    tracker = relationship('Tracker',backref='statuses')

    def __repr__(self):
        return self.name

transition_roles = Table('transition_roles',ModelBase.metadata,
        Column('transition_id',Integer,ForeignKey('tracker_transitions.id')),
        Column('role_id',Integer,ForeignKey('tracker_roles.id'))
        )

transition_emails = Table('transition_emails',ModelBase.metadata,
        Column('transition_id',Integer,ForeignKey('tracker_transitions.id')),
        Column('emailtemplate_id',Integer,ForeignKey('emailtemplates.id'))
        )

class TrackerTransition(ModelBase):
    __tablename__ = 'tracker_transitions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    label = Column(String(50))
    email_ids = Column(Text)
    display_fields = Column(Text)
    edit_fields = Column(Text)
    postpage = Column(Text)

    roles = relationship('TrackerRole',secondary=transition_roles,backref=backref('transitions',lazy='dynamic'))

    emails = relationship('EmailTemplate',secondary=transition_emails,backref=backref('transitions',lazy='dynamic'))

    tracker_id = reference_col('trackers')
    tracker = relationship('Tracker',backref='transitions')

    prev_status_id = reference_col('tracker_statuses',nullable=True)
    prev_status = relationship('TrackerStatus',backref='prev_transitions',foreign_keys=[prev_status_id])

    next_status_id = reference_col('tracker_statuses',nullable=True)
    next_status = relationship('TrackerStatus',backref='next_transitions',foreign_keys=[next_status_id])

    def __repr__(self):
        return self.name

    def edit_fields_list(self):
        pfields = []
        if self.edit_fields:
            pfields = self.edit_fields.split(',') if self.edit_fields else []
        rfields = []
        for pfield in pfields:
            rfield = dbsession.query(TrackerField).filter_by(tracker=self.tracker,name=pfield.strip()).first()
            if rfield:
                rfields.append(rfield)
        return rfields

    def display_fields_list(self):
        pfields = []
        if self.display_fields:
            pfields = self.display_fields.split(',')
        rfields = []
        for pfield in pfields:
            rfield = dbsession.query(TrackerField).filter_by(tracker=self.tracker,name=pfield.strip()).first()
            if rfield:
                rfields.append(rfield)
        return rfields

    def renderemails(self,request,data):
        if self.emails:
            for email in self.emails:
                email.renderemail(request,data=data)
