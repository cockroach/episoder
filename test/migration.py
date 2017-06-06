# episoder, https://github.com/cockroach/episoder
# -*- coding: utf8 -*-
#
# Copyright (C) 2004-2017 Stefan Ott. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from os import unlink
from tempfile import mktemp
from unittest import TestCase, TestLoader, TestSuite

from sqlalchemy import create_engine, MetaData, Table, Sequence, DateTime, Date
from sqlalchemy import Column, Integer, Text, Boolean
from sqlalchemy.engine import reflection
from sqlalchemy.orm import create_session

from pyepisoder.episoder import Database
from pyepisoder.database import Show, Meta


class MigrationTest(TestCase):

	def setUp(self):

		logging.basicConfig(level=logging.ERROR)
		logging.disable(logging.ERROR)

		self.path = mktemp()
		self.tempfiles = [self.path]

	def tearDown(self):

		for f in self.tempfiles:
			unlink(f)

	def _get_engine(self):

		return create_engine("sqlite:///%s" % self.path)

	def _set_schema_version(self, engine, version):

		meta = Meta()
		meta.key = "schema"
		meta.value = "%d" % version

		session = create_session(engine)
		session.begin()
		session.add(meta)
		session.commit()
		session.close()

	def _migrate(self, filename):

		db = Database(filename)
		db.migrate()
		db.close()

	def _create_custom(self):

		engine = self._get_engine()
		metadata = MetaData()
		metadata.bind = engine

		Table("shows", metadata,
			Column("my_int", Integer, primary_key=True)
		)

		Table("meta", metadata,
			Column("key", Text),
			Column("value", Text)
		)

		metadata.create_all()
		self._set_schema_version(engine, -1)
		engine.dispose()

	def _create_v1(self):

		engine = self._get_engine()
		metadata = MetaData()
		metadata.bind = engine

		Table("shows", metadata,
			Column("show_id", Integer, primary_key=True),
			Column("show_name", Text)
		)

		Table("episodes", metadata,
			Column("show_id", Integer),
			Column("num", Integer),
			Column("airdate", Integer),
			Column("season", Integer),
			Column("title", Text),
			Column("totalnum", Integer),
			Column("prodnum", Integer)
		)

		metadata.create_all()
		engine.dispose()

	def _create_v2(self):

		engine = self._get_engine()
		metadata = MetaData()
		metadata.bind = engine

		Table("shows", metadata,
			Column("show_id", Integer,
				Sequence("shows_show_id_seq"),
				primary_key=True),
			Column("show_name", Text),
			Column("url", Text),
			Column("updated", DateTime)
		)

		Table("meta", metadata,
			Column("key", Text),
			Column("value", Text)
		)

		Table("episodes", metadata,
			Column("show_id", Integer),
			Column("num", Integer),
			Column("airdate", Integer),
			Column("season", Integer),
			Column("title", Text),
			Column("totalnum", Integer),
			Column("prodnum", Integer)
		)

		metadata.create_all()
		self._set_schema_version(engine, 2)
		engine.dispose()

	def _create_v3(self):

		engine = self._get_engine()
		metadata = MetaData()
		metadata.bind = engine

		Table("shows", metadata,
			Column("show_id", Integer,
				Sequence("shows_show_id_seq"),
				primary_key=True),
			Column("show_name", Text),
			Column("url", Text),
			Column("updated", DateTime),
			Column("enabled", Boolean),
			Column("status", Integer, default=Show.RUNNING)
		)

		Table("meta", metadata,
			Column("key", Text),
			Column("value", Text)
		)

		Table("episodes", metadata,
			Column("show_id", Integer),
			Column("num", Integer),
			Column("airdate", Integer),
			Column("season", Integer),
			Column("title", Text),
			Column("totalnum", Integer),
			Column("prodnum", Integer)
		)

		metadata.create_all()
		self._set_schema_version(engine, 3)
		engine.dispose()

	def _create_v4(self):

		engine = self._get_engine()
		metadata = MetaData()
		metadata.bind = engine

		Table("shows", metadata,
			Column("show_id", Integer,
				Sequence("shows_show_id_seq"),
				primary_key=True),
			Column("show_name", Text),
			Column("url", Text),
			Column("updated", DateTime),
			Column("enabled", Boolean),
			Column("status", Integer, default=Show.RUNNING)
		)

		Table("meta", metadata,
			Column("key", Text),
			Column("value", Text)
		)

		Table("episodes", metadata,
			Column("show_id", Integer),
			Column("num", Integer),
			Column("airdate", Integer),
			Column("season", Integer),
			Column("title", Text),
			Column("totalnum", Integer),
			Column("prodnum", Integer),
			Column("notified", Date)
		)

		metadata.create_all()
		self._set_schema_version(engine, 4)
		engine.dispose()

	def _tables_dict(self, engine, table):

		inspector = reflection.Inspector.from_engine(engine)

		return { x["name"]: x for x in inspector.get_columns(table) }

	def test_migrate_from_v1(self):

		# Create version 1 database
		self._create_v1()

		# Verify
		engine = self._get_engine()
		self.assertTrue(engine.has_table("shows"))
		self.assertTrue(engine.has_table("episodes"))
		self.assertFalse(engine.has_table("meta"))
		engine.dispose()

		# Migrate to latest version
		self._migrate(self.path)

		# Check result - version 2 adds the "meta" table and shows.url
		engine = self._get_engine()
		self.assertTrue(engine.has_table("shows"))
		self.assertTrue(engine.has_table("episodes"))
		self.assertTrue(engine.has_table("meta"))

		columns = self._tables_dict(engine, "shows")
		self.assertIsNotNone(columns.get("url"))

		# Version 3 adds shows.enabled and shows.status
		self.assertIsNotNone(columns.get("enabled"))
		self.assertIsNotNone(columns.get("status"))

		# Version 4 adds episodes.notified
		columns = self._tables_dict(engine, "episodes")
		self.assertIsNotNone(columns.get("notified"))
		engine.dispose()

		# Check new schema version
		db = Database("sqlite:///%s" % self.path)
		self.assertEqual(4, db.get_schema_version())
		db.close()

	def test_migrate_from_v2(self):

		# Create version 2 database
		self._create_v2()

		# Verify
		engine = self._get_engine()
		self.assertTrue(engine.has_table("shows"))
		self.assertTrue(engine.has_table("episodes"))
		self.assertTrue(engine.has_table("meta"))

		columns = self._tables_dict(engine, "shows")
		self.assertIsNotNone(columns.get("url"))
		self.assertIsNone(columns.get("enabled"))
		self.assertIsNone(columns.get("status"))

		columns = self._tables_dict(engine, "episodes")
		self.assertIsNone(columns.get("notified"))
		engine.dispose()

		# Migrate to latest version
		self._migrate(self.path)

		# Check result - version 3 adds shows.enabled and shows.status
		engine = self._get_engine()
		columns = self._tables_dict(engine, "shows")
		self.assertIsNotNone(columns.get("enabled"))
		self.assertIsNotNone(columns.get("status"))

		# Version 4 adds episodes.notified
		columns = self._tables_dict(engine, "episodes")
		self.assertIsNotNone(columns.get("notified"))
		engine.dispose()

		# Check new schema version
		db = Database("sqlite:///%s" % self.path)
		self.assertEqual(4, db.get_schema_version())
		db.close()

	def test_migrate_from_v3(self):

		# Create version 3 database
		self._create_v3()

		# Verify
		engine = self._get_engine()
		self.assertTrue(engine.has_table("shows"))
		self.assertTrue(engine.has_table("episodes"))
		self.assertTrue(engine.has_table("meta"))

		columns = self._tables_dict(engine, "shows")
		self.assertIsNotNone(columns.get("url"))
		self.assertIsNotNone(columns.get("enabled"))
		self.assertIsNotNone(columns.get("status"))

		columns = self._tables_dict(engine, "episodes")
		self.assertIsNone(columns.get("notified"))
		engine.dispose()

		# Migrate to latest version
		self._migrate(self.path)

		# Version 4 adds episodes.notified
		engine = self._get_engine()
		columns = self._tables_dict(engine, "episodes")
		self.assertIsNotNone(columns.get("notified"))
		engine.dispose()

		db = Database("sqlite:///%s" % self.path)
		self.assertEqual(4, db.get_schema_version())
		db.close()

	def test_migrate_from_v4(self):

		# Create version 3 database
		self._create_v4()

		# Verify
		engine = self._get_engine()
		self.assertTrue(engine.has_table("shows"))
		self.assertTrue(engine.has_table("episodes"))
		self.assertTrue(engine.has_table("meta"))

		columns = self._tables_dict(engine, "shows")
		self.assertIsNotNone(columns.get("url"))
		self.assertIsNotNone(columns.get("enabled"))
		self.assertIsNotNone(columns.get("status"))

		columns = self._tables_dict(engine, "episodes")
		self.assertIsNotNone(columns.get("notified"))
		engine.dispose()

		# Migrate to latest version (noop)
		self._migrate(self.path)

		db = Database("sqlite:///%s" % self.path)
		self.assertEqual(4, db.get_schema_version())
		db.close()

	def test_disable_auto_migration(self):

		# Create a custom database
		self._create_custom()

		# Verify
		engine = self._get_engine()
		self.assertTrue(engine.has_table("shows"))
		self.assertFalse(engine.has_table("episodes"))
		self.assertTrue(engine.has_table("meta"))

		columns = self._tables_dict(engine, "shows")
		self.assertIsNotNone(columns.get("my_int"))
		self.assertIsNone(columns.get("url"))
		self.assertIsNone(columns.get("enabled"))
		self.assertIsNone(columns.get("status"))
		engine.dispose()

		# Migrate to latest version -> noop
		self._migrate(self.path)

		# Check result
		engine = self._get_engine()
		self.assertTrue(engine.has_table("shows"))
		self.assertFalse(engine.has_table("episodes"))
		self.assertTrue(engine.has_table("meta"))

		columns = self._tables_dict(engine, "shows")
		self.assertIsNotNone(columns.get("my_int"))
		self.assertIsNone(columns.get("url"))
		self.assertIsNone(columns.get("enabled"))
		self.assertIsNone(columns.get("status"))
		engine.dispose()

		# Check new schema version
		db = Database("sqlite:///%s" % self.path)
		self.assertEqual(-1, db.get_schema_version())
		db.close()

def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(MigrationTest))
	return suite
