# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from database import ModelBase, dbsession, reference_col
from sqlalchemy import column, Column, ForeignKey, Integer, String, Text, Boolean, Date, Table, MetaData, select
from sqlalchemy.orm import relationship, backref
from template import render_string

class Tracker(ModelBase):
    __tablename__ = 'trackers'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100),unique=True)
    module = Column(String(100),default='pages')
    list_fields = Column(Text)

    def __repr__(self):
        return self.title

    def list_fields_list(self):
        if self.list_fields:
            pfields = self.list_fields.split(',')
            rfields = []
            for pfield in pfields:
                print("pfield:" + pfield)
                rfield = dbsession.query(TrackerField).filter_by(tracker=self,name=pfield.strip()).first()
                if rfield:
                    rfields.append(rfield)
            return rfields

    def data_table(self):
        return "trak_" + self.slug + "_data"

    def update_table(self):
        return "trak_" + self.slug + "_updates"

    def field(self, name):
        field = dbsession.query(TrackerField).filter_by(tracker=self,name=name.strip()).first()
        return field

    def updatedb(self):
        query = """
            do $$
            begin
            if (select to_regclass('public.""" + self.data_table() + """_id_seq')) is null
            then
                create sequence public.""" + self.data_table() + """_id_seq
                increment 1
                minvalue 1
                maxvalue 9223372036854775807
                start 1
                cache 1;
            end if;
            if (select to_regclass('public.""" + self.data_table() + """')) is null
            then
                create table public.""" + self.data_table() + """(
                    id integer not null default nextval('""" + self.data_table() + """_id_seq'::regclass),
                    record_status character varying(50) 
                );
            end if;
            end$$;
        """
        print(query)
        dbsession.execute(query)
        dbsession.commit()
        for field in self.fields:
            field.updatedb()

    def addrecord(self, form):
        print(str(form))
        fieldnames = list(form.keys())
        query = """
            insert into """ + self.data_table() + """ ( """ + ",".join(fieldnames) + """) values 
            (""" + ",".join([ self.field(formfield).sqlvalue(form[formfield][0]) for formfield in fieldnames  ]) + """)
        """
        print(query)
        dbsession.execute(query)
        dbsession.commit()

    def records(self):
        results = None
        select_st = select([ field.dbcolumn() for field in self.list_fields_list() ]).select_from(self.data_table())
        print(select_st)
        results = dbsession.execute(select_st)
        return results

class TrackerField(ModelBase):
    __tablename__ = 'tracker_fields'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    label = Column(String(50))
    field_type = Column(String(20))

    tracker_id = reference_col('trackers')
    tracker = relationship('Tracker',backref='fields')

    def __repr__(self):
        return self.label

    def sqlvalue(self, value):
        print("val:" + str(value))
        if self.field_type in ['string','text','date','datetime']:
            return "'" + str(value) + "'"
        elif self.field_type in ['integer','number']:
            return str(value)
        elif self.field_type=='boolean':
            if value:
                return str(1)
            else:
                return str(0)

    def dbcolumn(self):
        return column(self.name)

    def db_field_type(self):
        if self.field_type=='string':
            return 'character varying(200)'
        elif self.field_type=='text':
            return 'text'
        elif self.field_type=='integer':
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
        query = """
            do $$
            begin 
                IF not EXISTS (SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema='public' and table_name='""" + self.tracker.data_table() + """' and column_name='""" + self.name + """') THEN
                        alter table public.""" + self.tracker.data_table() + """ add column """ + self.name + " " + self.db_field_type() + """ null ;
                end if;
            end$$;
        """
        print(query)
        dbsession.execute(query)
        dbsession.commit()

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

class TrackerTransition(ModelBase):
    __tablename__ = 'tracker_transitions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    display_fields = Column(Text)
    edit_fields = Column(Text)

    roles = relationship('TrackerRole',secondary=transition_roles,backref=backref('transitions',lazy='dynamic'))

    tracker_id = reference_col('trackers')
    tracker = relationship('Tracker',backref='transitions')

    prev_status_id = reference_col('tracker_statuses',nullable=True)
    prev_status = relationship('TrackerStatus',backref='prev_transitions',foreign_keys=[prev_status_id])

    next_status_id = reference_col('tracker_statuses',nullable=True)
    next_status = relationship('TrackerStatus',backref='next_transitions',foreign_keys=[next_status_id])

    def __repr__(self):
        return self.name

    def edit_fields_list(self):
        pfields = self.edit_fields.split(',')
        rfields = []
        for pfield in pfields:
            print("pfield:" + pfield)
            rfield = dbsession.query(TrackerField).filter_by(tracker=self.tracker,name=pfield.strip()).first()
            if rfield:
                rfields.append(rfield)
        return rfields

    def display_fields_list(self):
        pfields = self.display_fields.split(',')
        rfields = []
        for pfield in pfields:
            rfield = dbsession.query(TrackerField).filter_by(tracker=self.tracker,name=pfield.strip()).first()
            if rfield:
                rfields.append(rfield)
        return rfields
