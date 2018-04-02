#!/usr/bin/env python3
# -*- coding: utf-8 -*-



__author__ = 'guodong'

from orm import Model, StringField, IntegerField

class User(Model):
	__table__ = 'users'

	id = IntegerField(primary_key=True)
	name = StringField()


#创建实例
user = User(id=123, name='果冻')
#存入数据库
user.insert()
#查询所有User对象
users = User.findAll()
		