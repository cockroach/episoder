import json


class RawWrapper(object):

	def __init__(self, text):

		self._text = text

	def read(self):

		return self._text


class MockResponse(object):

	def __init__(self, data, encoding, status=200):

		self.raw = RawWrapper(data)
		self.encoding = encoding
		self.status_code = status

	def _get_text(self):

		text = self.raw.read()
		return text.decode(self.encoding, "replace")

	def json(self):

		return json.loads(self.text)


	text = property(_get_text)


