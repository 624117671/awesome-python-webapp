#!/usr/bin/env python3
# -*- coding: utf-8 -*-



__author__ = 'guodong'

import asyncio, logging
import aiomysql


def log(sql, args=()):
	logging.info('SQL: %s' % sql)




#创建连接池
@asyncio.coroutine
def create_pool(loop, **kw):
	logging.info('创建数据库连接池')
	global _pool
	_pool = yield from aiomysql.create_pool(
		host = kw.get('host','localhost'),
		port = kw.get('port', 3306),
		user = kw['user'],
		password = kw['password'],
		db = kw['db'],
		charset = kw.get('charset','utf-8'),
		autocommit = kw.get('autocommit',True),
		maxsize = kw.get('maxsize',10),
		minsize = kw.get('minsize',1),
		loop = loop
	)
@asyncio.coroutine
def select(sql,args,size=None):
	log(sql,args)
	global _pool
	with (yield from _pool) as conn:
		cur = yield from conn.cursor(aiomysql.DictCursor)
		yield from cur.execute(sql.replace('?','%s'), args or ())
		if size:
			rs = yield from cur.fetchmany(size)
		else:
			rs = yield from cur.fetchall
		yield from cur.close()
		logging.info('rows returned: %s' % len(rs))
		return rs


@asyncio.coroutine
def excute(sql,args):
	log(sql)
	with (yield from _pool) as conn:
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?','%s'),args)
			affected = cur.rowcount
			yield from cur.close()
		except Exception as e:
			raise e
		return affected


class Model(dict, metaclass=ModelMetaclass):
	"""docstring for Model"""
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'MOdel' object has no attribute '%s'" % key)

	def __setattr__(self, key, value):
		self[key] = value

	def getValue(self, key):
		return getattr(self, key, None)

	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug("using default value for %s" % (key, str(value)))
				setattr(self, key, value)
		return value
		


class Field(object):
	"""docstring for Field"""
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default

	def __str__(self):
		return '<%s, %s, %s>' % (self.__class__.__name__, self.column_type, self.name)

class StringField(Field):
	"""docstring for StringField"""
	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		super().__init__()
		self.arg = arg
		
class  ModelMetaclass(type):
	"""docstring for  ModelMetaclass"""
	def __new__(cls, name, bases, attrs):
		#排除Model类本身
		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)
		#获取table名称
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table: %s)' % (name, tableName))
		#获取所有的filed和主键名
		mappings = dict()
		fields = []
		primaryKey = None
		for k, v in attrs.items():
			if isinstance(v,Fild):
				logging.info('found mappings: %s ==> %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					raise RuntimeError('Duplicate primary key for filed: %s' % k)
				primaryKey = k
			else:
				fields.append(k)
		if not primaryKey:
			raise RuntimeError('primary key not found')
		for k in mappings.keys():
			attrs.pop(k)
		escaped_fields = list(map(lambda f: '%s' % f, fields))
		attrs['__mappings__'] = mappings  #保存属性和列的映射关系
		attrs['__table__'] = tableName 
		attrs['__primary_key__'] = primaryKey #主键属性
		attrs['__fields__'] = fields  #除主键外其他属性名
		#构造默认的select insert update 和delete语句
		attrs['__select__']

		