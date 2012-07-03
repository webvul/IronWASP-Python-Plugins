#Author: Lavakumar Kuppan
#License: MIT License - http://www.opensource.org/licenses/mit-license

from IronWASP import *
from System import *
import clr

class CrossSiteScripting(ActivePlugin):
    
	def GetInstance(self):
		p = CrossSiteScripting()
		p.Name = "Cross-site Scripting"
		p.Version = "0.2"
		p.Description = "Active Plugin to detect Cross-site Scripting vulnerabilities"
		return p
	
	def Check(self, Scnr):
		self.Scnr = Scnr
		self.base_req = self.Scnr.BaseRequest
		self.base_res = self.Scnr.BaseResponse
		self.Confidence = 0
		self.RequestTriggers = []
		self.ResponseTriggers = []
		self.TriggerRequests = []
		self.TriggerResponses = []

		self.Scnr.StartTrace()
		self.Scnr.SetTraceTitle("-",0)
		#Send a Random string for analysing injection nature
		#ps = self.GetProbeString()
		self.ps = Analyzer.GetProbeString()
		
		
		self.Scnr.Trace("<i<br>><i<h>>Checking Reflection Contexts with a Probe String:<i</h>>")
		self.Scnr.RequestTrace("  Injected Probe String - {0}".format(self.ps))
		
		self.ps_res = self.Scnr.Inject(self.ps)
		self.ps_req = self.Scnr.InjectedRequest.GetClone()
		#Store the ProbeString in Analyzer for Stored XSS Reflection Checking
		Analyzer.AddProbeString(self.ps, self.Scnr.InjectedRequest)
		
		res_details = "		|| Code - {0} | Length - {1}".format(self.ps_res.Code, self.ps_res.BodyLength)
		if(self.ps_res.BodyString.Contains(self.ps)):
			self.ps_contexts = self.GetContext(self.ps, self.ps_res)
			self.ps_contexts = list(set(self.ps_contexts))#make the array unique
		else:
			self.ps_contexts = []
		
		ps_contexts_string = ""
		if(len(self.ps_contexts) == 0):
			ps_contexts_string = "<i<cg>>No reflection<i</cg>>"
		else:
			ps_contexts_string = "<i<cr>>{0}<i</cr>>".format(",".join(self.ps_contexts))
		self.Scnr.ResponseTrace(" ==> Reflection contexts - {0}{1}".format(ps_contexts_string, res_details))
		
		self.CheckCharsetSecurity()
		self.CheckForCrossSiteCookieSetting()
		
		#Do Context specific checks
		for context in self.ps_contexts:
			if(context == "JS"):
				self.CheckForInjectionInFullJS()
			elif(context == "InLineJS" or context == "JSUrl" or context == "EventAttribute"):
				self.CheckForInjectionInJSInsideHTML()
			elif(context == "InLineVB"):
				self.CheckForInjectionInVBInsideHTML()
			elif(context == "UrlAttribute"):
				self.CheckForInjectionInUrlAttribute()
			elif(context == "CSS" or context == "InLineCSS"):
				self.CheckForInjectionInFullCSS()
			elif(context == "AttributeCSS"):
				self.CheckForInjectionInCSSInsideStyleAttribute()
			elif(context == "AttributeName"):
				self.CheckForInjectionInAttributeName()
			elif(context == "AttributeValueWithSingleQuote"):
				self.CheckForInjectionInSingleQuoteAttributeValue()
			elif(context == "AttributeValueWithDoubleQuote"):
				self.CheckForInjectionInDoubleQuoteAttributeValue()
		
		#Do a HTML Injection Check irrespective of the context
		self.CheckForInjectionInHtml()
		
		#Check for Injection in Special Attributes
		self.CheckForInjectionInSpecialAttributes()
		
		#Scan is complete, analyse the results
		self.AnalyseResults()
	
	def CheckForInjectionInHtml(self):
		contexts = ["HTML"]
		if self.ps_contexts.Contains("Unknown") or self.ps_contexts.Contains("AttributeName") or self.ps_contexts.Contains("AttributeValueWithSingleQuote") or self.ps_contexts.Contains("AttributeValueWithDoubleQuote"):
			contexts.append("HTML Escape")
		if self.ps_contexts.Contains("Textarea"):
			contexts.append("TEXTAREA tag")
		if self.ps_contexts.Contains("InLineJS"):
			contexts.append("SCRIPT tag")
		if self.ps_contexts.Contains("InLineCSS"):
			contexts.append("STYLE tag")
		if self.ps_contexts.Contains("Comment"):
			contexts.append("HTML Comment")
		
		for context in contexts:
			prefixes = []
			suffixes = []
			attr_names = ""
			attr_values = ""
			trace_header = ""
			trace_success = ""
			trace_fail = ""
			
			if context == "HTML":
				prefixes = [""]
				suffixes = [""]
				attr_name = "xhx"
				attr_value = "yhy"
				trace_header = "Checking HTML Injection in HTML Context"
				trace_success = "Got HTML injection in HTML Context"
				trace_fail = "Unable to inject HTML in HTML Context"
			elif context == "HTML Escape":
				prefixes = ["a\">", "a'>", "a>", "a\">", "a'>", "a>"]
				suffixes = ["<b\"", "<b'", "<b", "", "", ""]
				attr_name = "xex"
				attr_value = "yey"
				trace_header = "Checking HTML Injection by escaping in to HTML Context"
				trace_success = "Got HTML injection by escaping in to HTML Context"
				trace_fail = "Unable to inject HTML by escaping in to HTML Context"
			elif context == "TEXTAREA tag":
				prefixes = ["</textarea>"]
				suffixes = [""]
				attr_name = "xtx"
				attr_value = "yty"
				trace_header = "Checking HTML Injection by escaping Textarea tag Context"
				trace_success = "Got HTML injection by escaping Textarea tag Context"
				trace_fail = "Unable to inject HTML by escaping Textarea tag Context"
			elif context == "SCRIPT tag":
				prefixes = ["</script>", "--></script>"]
				suffixes = ["", ""]
				attr_name = "xjx"
				attr_value = "yjy"
				trace_header = "Checking HTML Injection by escaping Script tag Context"
				trace_success = "Got HTML injection by escaping Script tag Context"
				trace_fail = "Unable to inject HTML by escaping Script tag Context"
			elif context == "STYLE tag":
				prefixes = ["</style>", "--></style>"]
				suffixes = ["", ""]
				attr_name = "xsx"
				attr_value = "ysy"
				trace_header = "Checking HTML Injection by escaping Style tag Context"
				trace_success = "Got HTML injection by escaping Style tag Context"
				trace_fail = "Unable to inject HTML by escaping Style tag Context"
			elif context == "HTML Comment":
				prefixes = ["-->"]
				suffixes = [""]
				attr_name = "xcx"
				attr_value = "ycy"
				trace_header = "Checking HTML Injection by escaping HTML Comment Context"
				trace_success = "Got HTML injection by escaping HTML Comment Context"
				trace_fail = "Unable to inject HTML by escaping HTML Comment Context"
			
			self.Scnr.Trace("<i<br>><i<h>>{0}:<i</h>>".format(trace_header))
			for i in range(len(prefixes)):
				payload = "{0}<h {1}={2}>{3}".format(prefixes[i], attr_name, attr_value, suffixes[i])
				
				self.Scnr.RequestTrace("  Injected {0} - ".format(payload))
				res = self.Scnr.Inject(payload)
				
				res_details = "		|| Code - {0} | Length - {1}".format(res.Code, res.BodyLength)
				self.CheckResponseDetails(res)
				if len(res.Html.Get("h", attr_name, attr_value)) > 0:
					self.AddToTriggers(payload, payload)
					self.SetConfidence(3)
					self.Scnr.ResponseTrace("<i<cr>>{0}<i</cr>>{1}".format(trace_success, res_details))
				else:
					self.Scnr.ResponseTrace("{0}{1}".format(trace_fail, res_details))
		
	def CheckForInjectionInJSInsideHTML(self):
		self.CheckForInjectionInJS(True)
		
	def CheckForInjectionInFullJS(self):
		self.CheckForInjectionInJS(False)
			
	def CheckForInjectionInJS(self, InLine):
	
		script_contexts = []
		contaminated_scripts = []
		if(InLine):
			contaminated_scripts = self.ps_res.Html.GetJavaScript(self.ps)
		else:
			contaminated_scripts.append(self.ps_res.BodyString)

		payload_prefixes = []
		for script in contaminated_scripts:
			payload_prefixes.append(self.GetJSPayload(script))
			self.CheckSinkAssignment(script)
			script_contexts.extend(self.GetJSContexts(script))
		
		script_contexts = list(set(script_contexts))#make the array unique
		
		if script_contexts.count("NormalString") > 0:
			self.AddToTriggersWithProbeStringInjection(self.ps, self.ps)
			self.SetConfidence(1)
			self.Scnr.Trace("<i<cr>>Probe string is reflected inside JavaScript Script outside Quotes. Possibly vulnerable!<i</cr>>")
		
		if len(script_contexts) > 0:
			self.Scnr.Trace("<i<br>><i<b>>Got injection inside JavaScript as - {0}<i</b>>".format(",".join(script_contexts)))

		self.Scnr.Trace("<i<br>><i<h>>Checking for Injection in JS Context:<i</h>>")
		keyword = "dzkqivxy"
		js_inj_success = False
		for payload_prefix in payload_prefixes:
			binders = [";", "\n", "\r"]
			paddings = [";/*", ";//", "/*", "//"]
			payload_inj_success = False
			for binder in binders:
				for padding in paddings:
					if payload_inj_success:
						break
					payload = "{0}{1}{2}{3}".format(payload_prefix, binder, keyword, padding)
					self.Scnr.RequestTrace("  Injected {0} - ".format(payload))
					res = self.Scnr.Inject(payload)
					if self.IsExpressionStatement(res, keyword):
						self.Scnr.ResponseTrace("<i<cr>>Injected {0} as a JavaScript statement.<i</cr>>".format(keyword))
						self.AddToTriggers(payload, keyword)
						self.SetConfidence(3)
						payload_inj_success = True
						js_inj_success = True
					else:
						self.Scnr.ResponseTrace("Could not get {0} as JavaScript statement".format(keyword))
				
		if not js_inj_success:
			payload_prefixes = []
			if script_contexts.count("SingleQuotedString") > 0:
				payload_prefixes.append("'")
			if script_contexts.count("DoubleQuotedString") > 0:
				payload_prefixes.append('"')
			if script_contexts.count("SingleLineComment") > 0:
				payload_prefixes.append('\r')
				payload_prefixes.append('\n')
			if script_contexts.count("MutliLineComment") > 0:
				payload_prefixes.append('*/')
			keyword = "dzpyqmw"
			for pp in payload_prefixes:
				payload = "{0}{1}".format(pp, keyword)
				self.Scnr.RequestTrace("  Injected {0} - ".format(payload))
				res = self.Scnr.Inject(payload)
				if self.IsNormalString(res, keyword):
					self.Scnr.ResponseTrace("<i<cr>>Injected {0} as a JavaScript statement.<i</cr>>".format(keyword))
					self.AddToTriggers(payload, keyword)
					self.SetConfidence(2)
					js_inj_success = True
					break
				else:
					self.Scnr.ResponseTrace("Could not get {0} as JavaScript statement".format(keyword))
		if not js_inj_success:
			if script_contexts.count("NormalString") > 0:
				js_inj_success = True
		
		if not js_inj_success:
			self.ReportJSTestLead()
	
	def GetJSPayload(self, script):
		context_finishers = ['', ')', ']', '}', '))', ')]', ')}', '])', ']]', ']}', '})', '}]', '}}']
		context_finishers.extend([')))', '))]', '))}', ')])', ')]]', ')]}', ')})', ')}]', ')}}', ']))', '])]'])
		context_finishers.extend(['])}', ']])', ']]]', ']]}', ']})', ']}]', ']}}', '}))', '})]', '})}', '}])'])
		context_finishers.extend(['}]]', '}]}', '}})', '}}]', '}}}'])
		quotes = ["", "'", '"']
		padding = ";/*"
		keyword = "dzkqivxy"
		for cf in context_finishers:
			for q in quotes:
				payload_prefix = "{0}{1}".format(q, cf)
				payload = "{0};{1}{2}".format(payload_prefix, keyword, padding)
				script_updated = script.replace(self.ps, payload)
				try:
					if IronJint.IsExpressionStatement(script_updated, keyword):
						return payload_prefix
				except:
					pass
		return ""
	
	def CheckSinkAssignment(self, script):
		try:
			ij = IronJint.Trace(script, self.ps)
			if len(ij.SourceToSinkLines) > 0:
				self.Scnr.Trace("<i<br>><i<cr>><i<b>>Injected ProbeString was assigned to a DOM XSS Sink<i</b>><i</cr>>")
				js_triggers = []
				for line in ij.SourceToSinkLines:
					js_triggers.append(line)
				self.AddToTriggersWithProbeStringInjection(self.ps, "\r\n".join(js_triggers))
				self.SetConfidence(3)
		except:
			pass
	
	def GetJSContexts(self, script):
		script_contexts = []
		try:
			script_contexts.extend(CodeContext.GetJavaScriptContext(script, self.ps))
		except:
			pass
		return script_contexts
	
	def IsExpressionStatement(self, res, keyword):
		scripts = []
		if res.IsJavaScript:
			if res.BodyString.count(keyword) > 0:
				scripts.append(res.BodyString)
		elif res.IsHtml:
			scripts = res.Html.GetJavaScript(keyword)
		
		for script in scripts:
			try:
				if IronJint.IsExpressionStatement(script, keyword):
					return True
			except:
				pass
		return False
	
	def IsNormalString(self, res, keyword):
		scripts = []
		if res.IsJavaScript:
			if res.BodyString.count(keyword) > 0:
				scripts.append(res.BodyString)
		elif res.IsHtml:
			scripts = res.Html.GetJavaScript(keyword)
		
		for script in scripts:
			try:
				script_contexts = []
				script_contexts.extend(CodeContext.GetJavaScriptContext(script, keyword))
				if script_contexts.count("NormalString"):
					return True
			except:
				pass
		return False
	
	def CheckForInjectionInVBInsideHTML(self):
		self.Scnr.Trace("<i<br>><i<h>>Checking for Script Injection inside VB Script Tag:<i</h>>")
		script_contexts = []
		contaminated_scripts = self.ps_res.Html.GetVisualBasic(self.ps)

		for script in contaminated_scripts:
			script_contexts.extend(self.GetVBContexts(script))
		
		script_contexts = list(set(script_contexts))#make the array unique
		if script_contexts.count("NormalString") > 0:
			self.AddToTriggersWithProbeStringInjection(self.ps, self.ps)
			self.SetConfidence(1)
			self.Scnr.Trace("<i<cr>>Probe string is reflected inside VB Script outside Quotes. Possibly vulnerable!<i</cr>>")
		
		if len(script_contexts) > 0:
			self.Scnr.Trace("<i<br>><i<b>>Got injection inside VB Script as - {0}<i</b>>".format(",".join(script_contexts)))
		
		payload_prefixes = [""]
		if script_contexts.count("DoubleQuotedString") > 0:
			payload_prefixes.append('"')
		if script_contexts.count("SingleLineComment") > 0:
			payload_prefixes.append('\n')
		keyword = "dzpxqmw"
		vb_inj_success = False
		for pp in payload_prefixes:
			payload = "{0}{1}".format(pp, keyword)
			self.Scnr.RequestTrace("  Injected {0} - ".format(payload))
			res = self.Scnr.Inject(payload)
			if self.IsNormalVBString(res, keyword):
				self.Scnr.ResponseTrace("<i<cr>>Injected {0} as a VB statement.<i</cr>>".format(keyword))
				self.AddToTriggers(payload, keyword)
				self.SetConfidence(2)
				vb_inj_success = True
				break
			else:
				self.Scnr.ResponseTrace("Could not get {0} as JavaScript statement".format(keyword))
	
	def GetVBContexts(self, script):
		script_contexts = []
		try:
			script_contexts.extend(CodeContext.GetVisualBasicContext(script, self.ps))
		except:
			pass
		return script_contexts
	
	def IsNormalVBString(self, res, keyword):
		scripts = []
		if res.IsHtml:
			scripts = res.Html.GetVisualBasic(keyword)
		for script in scripts:
			try:
				script_contexts = []
				script_contexts.extend(CodeContext.GetVisualBasicContext(script, keyword))
				if script_contexts.count("NormalString"):
					return True
			except:
				pass
		return False
	
	def CheckForInjectionInUrlAttribute(self):
		#Start the test
		self.Scnr.Trace("<i<br>><i<h>>Checking JS Injection in UrlAttribute Context:<i</h>>")
		self.Scnr.RequestTrace("  Injected javascript:yhstdjbz - ")
		
		ua_res = self.Scnr.Inject("javascript:yhstdjbz")
		
		res_details = "		|| Code - {0} | Length - {1}".format(str(ua_res.Code), str(ua_res.BodyLength))
		self.CheckResponseDetails(ua_res)
		
		if ua_res.BodyString.Contains("javascript:yhstdjbz") or (ua_res.Headers.Has("Refresh") and ua_res.Headers.Get("Refresh").count("javascript:yhstdjbz") > 0):
			ua_inj_contexts = self.GetContext("yhstdjbz", ua_res)
			if ua_inj_contexts.Contains("JSUrl"):
				self.Scnr.ResponseTrace("<i<cr>>Got yhstdjbz in InLineJS context<i</cr>>{0}".format(res_details))
				self.AddToTriggers("javascript:yhstdjbz","javascript:yhstdjbz")
				self.SetConfidence(3)
			else:
				self.Scnr.ResponseTrace("Got javascript:yhstdjbz in non-UrlAttribute context")
		else:
			#must check for the encoding here
			self.Scnr.ResponseTrace("No reflection{0}".format(res_details))

	def CheckForInjectionInAttributeName(self):		
		#Start the test
		self.Scnr.Trace("<i<br>><i<h>>Checking for Injection in HTML AttributeName Context:<i</h>>")
		self.InjectAttribute(" olpqir=\"vtkir(1)\"","olpqir","vtkir(1)")
		self.InjectAttribute(" olpqir='vtkir(1)'","olpqir","vtkir(1)")
	
	
	def CheckForInjectionInSpecialAttributes(self):
		self.Scnr.Trace("<i<br>><i<h>>Checking for Injection in Special HTML Attributes:<i</h>>")
		
		self.CheckForSameSiteScriptIncludeSetting()
		
		host = self.base_req.Host
		#remove the port number from hostname
		try:
			if host.index(":") > 0:
				host = host[:host.index(":")]
		except:
			pass
		self.Scnr.Trace("<i<br>><i<b>>Checking for Reflection inside Special HTML Attributes:<i</b>>")
		initial_payloads = [ "fpwzyqmc", "http://{0}.fpwzyqmc".format(host), "https://{0}.fpwzyqmc".format(host), "//{0}.fpwzyqmc".format(host)]
		eligible = False
		for i_p in initial_payloads:
			self.Scnr.RequestTrace("  Injected {0} ==> ".format(i_p))
			res = self.Scnr.Inject(i_p)
			if self.IsInSpecialAttribute(i_p, res):
				eligible = True
				self.Scnr.ResponseTrace("  Found reflection inside Special HTML Attributes")
				break
			else:
				self.Scnr.ResponseTrace("  Not reflected inside Special HTML Attributes")
		if not eligible:
			self.Scnr.Trace("<i<br>>  No reflection found inside Special HTML Attributes")
			return
		
		self.Scnr.Trace("<i<br>><i<b>>Checking for Payload Injection inside Special HTML Attributes:<i</b>>")
		sign_str = "olxizrk"
		self.injectable_special_tags = []
		self.injectable_special_attributes = []
		#prefixes taken from http://kotowicz.net/absolute/
		prefixes = [ "http://", "https://", "//", "http:\\\\", "https:\\\\", "\\\\", "/\\", "\\/", "\r//", "/ /", "http:", "https:", "http:/", "https:/", "http:////", "https:////", "://", ".:."]

		all_tags_and_attrs = []
		for prefix in prefixes:
			for ii in range(2):
				if ii == 0:
					payload = "{0}{1}".format(prefix, sign_str)
				else:
					payload = "{0}{1}.{2}".format(prefix, host, sign_str)
				self.Scnr.RequestTrace("  Injected {0} ==> ".format(payload))
				res = self.Scnr.Inject(payload)
				if self.IsInSpecialAttribute(payload, res):
					all_tags_and_attrs = []
					for i in range(len(self.injectable_special_tags)):
						all_tags_and_attrs.append("	{0}) <i<b>>{1}<i</b>> attribute of <i<b>>{2}<i</b>> tag".format(i + 1, self.injectable_special_tags[i], self.injectable_special_attributes[i]))
					self.Scnr.ResponseTrace("<i<cr>>Got {0} inside the following Special HTML Attributes:<i</cr>><i<br>>{1}".format(payload, "<i<br>>".join(all_tags_and_attrs)))
					if self.injectable_special_tags.count("script") > 0:
						self.AddToTriggers(payload, payload)
						self.SetConfidence(3)
						self.Scnr.Trace("<i<br>><i<cr>>Able to set the source attribute of the Script tag to remote URL and include rogue JavaScript<i</cr>>")
					elif self.injectable_special_tags.count("object") > 0:
						self.AddToTriggers(payload, payload)
						self.SetConfidence(3)
						self.Scnr.Trace("<i<br>><i<cr>>Able to set the data attribute of the Object tag to remote URL and include rogue active components like SWF files<i</cr>>")
					elif self.injectable_special_tags.count("embed") > 0:
						self.AddToTriggers(payload, payload)
						self.SetConfidence(3)
						self.Scnr.Trace("<i<br>><i<cr>>Able to set the href attribute of the Embed tag to remote URL and include rogue active components like SWF files<i</cr>>")
					elif self.injectable_special_tags.count("link") > 0:
						self.AddToTriggers(payload, payload)
						self.SetConfidence(3)
						self.Scnr.Trace("<i<br>><i<cr>>Able to set the href attribute of the Link tag to remote URL and include rogue CSS that can contain JavaScript<i</cr>>")
					else:
						self.ReportInjectionInSpecialAttributes(payload)
					return
				else:
					res_details = "		|| Code - {0} | Length - {1}".format(res.Code, res.BodyLength)
					self.Scnr.ResponseTrace("Did not get payload inside the Special HTML Attributes{0}".format(res_details))

				
	def CheckForSameSiteScriptIncludeSetting(self):
		scripts = []
		styles = []
		scripts_vuln = []
		styles_vuln = []
		if self.ps_res.IsHtml:
			scripts = self.ps_res.Html.GetValues("script", "src")
			styles = self.ps_res.Html.GetValues("link", "href")
		for script in scripts:
			if self.IsInUrlPath(script, self.ps):
				scripts_vuln.append(script)
		for style in styles:
			if self.IsInUrlPath(style, self.ps):
				styles_vuln.append(style)
		if (len(scripts_vuln) + len(styles_vuln)) > 0:
			self.Scnr.Trace("<i<br>><i<cr>>Able to influence the location of the in-domain JS/CSS inlcuded in the page.<i</cr>>")
			self.ReportSameSiteScriptInclude(scripts_vuln, styles_vuln)
	
	def IsInUrlPath(self, url, keyword):
		try:
			full_url = ""
			if url.startswith("http://") or url.startswith("https://"):
				full_url = url
			else:
				full_url = "http://a/{0}".format(url)
			r = Request(full_url)
			if r.UrlPath.count(keyword) > 0:
				return True
		except:
			pass
		return False
	
	def IsInSpecialAttribute(self, keyword, res):
		special_tags = [ "iframe", "script", "link", "object", "embed", "form", "button", "base", "a"]
		special_attributes = [ "src", "src", "href", "data", "src", "action", "formaction", "href", "href"]
		
		self.injectable_special_tags = []
		self.injectable_special_attributes = []
		
		for i in range(len(special_tags)):
			tag_name = special_tags[i]
			tag_attr = special_attributes[i]
			values = res.Html.GetValues(tag_name, tag_attr)
			for value in values:
				if value.startswith(keyword):
					self.injectable_special_tags.append(tag_name)
					self.injectable_special_attributes.append(tag_attr)
					break
		if len(self.injectable_special_tags) > 0:
			return True
		else:
			return False
	
	def CheckForInjectionInSingleQuoteAttributeValue(self):
		self.Scnr.Trace("<i<br>><i<h>>Checking for Injection in HTML AttributeValue Context:<i</h>>")
		self.InjectAttribute(" \' olqpir=\"vtikr(1)\"","olqpir","vtikr(1)")
		self.InjectAttribute(" \' olqpir=\'vtikr(1)\'","olqpir","vtikr(1)")
	
	def CheckForInjectionInDoubleQuoteAttributeValue(self):
		self.Scnr.Trace("<i<br>><i<h>>Checking for Injection in HTML AttributeValue Context:<i</h>>")
		self.InjectAttribute(" \" olqpir=\"vtikr(1)\"","olqpir","vtikr(1)")
		self.InjectAttribute(" \" olqpir=\'vtikr(1)\'","olqpir","vtikr(1)")
		#HtmlAgilityPack considers quote-less as Double-Quote
		self.InjectAttribute(" olqpir=\"vtikr(1)\"","olqpir","vtikr(1)")
		self.InjectAttribute(" olqpir=\'vtikr(1)\'","olqpir","vtikr(1)")
		self.InjectAttribute("aa olqpir=\"vtikr(1)\"","olqpir","vtikr(1)")
		self.InjectAttribute("aa olqpir=\'vtikr(1)\'","olqpir","vtikr(1)")
	
	def InjectAttribute(self, Payload, AttrName, AttrValue):		
		#Start the test
		self.Scnr.RequestTrace("  Injected {0} - ".format(Payload))
		
		at_res = self.Scnr.Inject(Payload)
		res_details = "		|| Code - {0} | Length - {1}".format(str(at_res.Code), str(at_res.BodyLength))
		self.CheckResponseDetails(at_res)
		
		name_contexts = self.GetContext(AttrName, at_res)
		value_contexts = self.GetContext(AttrValue, at_res)
		if(name_contexts.Contains("AttributeName") and (value_contexts.Contains("AttributeValueWithSingleQuote") or value_contexts.Contains("AttributeValueWithDoubleQuote"))):
			self.Scnr.ResponseTrace("<i<cr>>Got {0} as AttributeName and {1} as AttributeValue<i</cr>>{2}".format(AttrName, AttrValue, res_details))
			self.AddToTriggers(Payload, Payload)
			self.SetConfidence(3)
 		elif(at_res.BodyString.Contains(Payload)):
 			self.Scnr.ResponseTrace("Got {0} outside of AttributeName and AttributeValue context{1}".format(Payload, res_details))
 		else:
			self.Scnr.ResponseTrace("No useful reflection{0}".format(res_details))
	
	
	def CheckForInjectionInCSSInsideStyleAttribute(self):
		self.CheckForInjectionInCSS(True)
		
	def CheckForInjectionInFullCSS(self):
		self.CheckForInjectionInCSS(False)
			
	def CheckForInjectionInCSS(self, InStyleAttribute):
		css_contexts = self.GetCssContexts(self.ps, self.ps_res)
		for context in css_contexts:
			self.CheckForInjectionInCSSContext(context, InStyleAttribute)
	
	def GetCssContexts(self, keyword, res):
		css_contexts = []
		contaminated_css = []
		if res.IsHtml:
			contaminated_css = res.Html.GetCss(keyword, True)
		elif res.IsCss:
			contaminated_css.append(res.BodyString)
		for css in contaminated_css:
			try:
				css_contexts.extend(IronCss.GetContext(css, keyword))
			except:
				pass
		css_contexts = list(set(css_contexts))
		return css_contexts
	
	def CheckForInjectionInCSSContext(self, css_context, InStyleAttribute):
		payload = ""
		url_special_payloads = []
		jsurl_special_payloads = []
		js_special_payloads = []
		quote = ""
		
		context_parts = css_context.split("-")
		#
		#CSS Value contexts
		#
		if context_parts[0] == "Value":
			quote = context_parts[3]
			if context_parts[1] == "Normal" or context_parts[1] == "OnlyNormal":
				payload = "aa<quote>;} <vector> aa {aa:<quote>aa"
				jsurl_special_payloads.append("aa<quote>; background-image: url(<url>); aa:<quote>aa")
				js_special_payloads.append("aa<quote>; aa: expression('<js>'); aa:<quote>aa")
				js_special_payloads.append('aa<quote>; aa: expression("<js>"); aa:<quote>aa')
				if context_parts[1] == "OnlyNormal":
					if context_parts[2] == "Full":
						js_special_payloads.append("expression('<js>')")
					elif context_parts[2] == "Start":
						js_special_payloads.append("expression('<js>'); aa:")
			elif context_parts[1] == "JS":
				#report as xss
				pass
			elif context_parts[1] == "Url":
				payload = "aa<quote>);} <vector> aa {aa:<quote>url(aa"
				jsurl_special_payloads.append("aa<quote>); background-image: url(<url>); aa:url(<quote>aa")
				js_special_payloads.append("aa<quote>); aa: expression('<js>'); aa:url(<quote>aa")
				js_special_payloads.append('aa<quote>); aa: expression("<js>"); aa:url(<quote>aa')
				if context_parts[2] == "Start" or context_parts[2] == "Full":
					jsurl_special_payloads.append("<url>")
		#
		#CSS Propery contexts
		#
		elif context_parts[0] == "Property":
			payload = "aa:aa} <vector> aa {aa"
			if context_parts[1] == "Start" or context_parts[1] == "Full":
				jsurl_special_payloads.append("background-image:url(<url>); aa")
				js_special_payloads.append("aa:expression('<js>'); aa")
				js_special_payloads.append('aa:expression("<js>"); aa')
		#
		#CSS Ident contexts
		#
		elif context_parts[0] == "Ident":
			if context_parts[1] == "Ident":
				payload = "aa {x:x} <vector> @aa"
				if context_parts[2] == "Start" or context_parts[2] == "Full":
					url_special_payloads.append("import '<url>'; @a")
					url_special_payloads.append('import "<url>"; @a')
					jsurl_special_payloads.append("import '<url>'; @a")
					jsurl_special_payloads.append('import "<url>"; @a')
			elif context_parts[1] == "MediaValue":
				payload = "aa {x {x:x}} <vector> @media aa"
		#
		#CSS Import contexts
		#
		elif context_parts[0] == "Import":
			quote = context_parts[3]
			if context_parts[1] == "Raw":
				payload = "aa<quote>; <vector> @import <quote>aa"
				if context_parts[2] == "Start" or context_parts[2] == "Full":
					url_special_payloads.append("<url>")
					jsurl_special_payloads.append("<url>")
					#report as xss
			elif context_parts[1] == "Url":
				payload = "aa<quote>); <vector> @import url(<quote>aa"
				if context_parts[2] == "Start" or context_parts[2] == "Full":
					url_special_payloads.append("<url>")
					jsurl_special_payloads.append("<url>")
					#report as xss
			elif context_parts[1] == "RawJS":
				#report as xss
				pass
			elif context_parts[1] == "UrlJS":
				#report as xss
				pass
			pass
		#
		#CSS Selector contexts
		#
		elif context_parts[0] == "Selector":
			if context_parts[1] == "Normal":
				if context_parts[2] == "Start" or context_parts[2] == "Full":
					payload = "<vector> aa"
				else:
					payload = "aa {aa:aa} <vector> aa"
			elif context_parts[1] == "Round":
				payload = "aa) {aa:aa} <vector> aa(aa"
			elif context_parts[1] == "SquareKey":
				payload = "aa=aa] {aa:aa} <vector> aa[aa"
			elif context_parts[1] == "SquareValue":
				payload = "aa<quote>] {aa:aa} <vector> aa[aa=<quote>aa"
		#
		#CSS Comment contexts
		#
		elif context_parts[0] == "Comment":
			payload = "*/ <vector> /*"
		
		payload = self.InsertCssQuotes(quote, payload)
		
		url_vectors = ["@import '//iczpbtsq';", '@import "//iczpbtsq";', "@import url(//iczpbtsq);"]
		js_vectors = ["@import 'javascript:\"iczpbtsq\"';", '@import "javascript:\'iczpbtsq\'";']
		js_vectors.extend(["@import url(javascript:'iczpbtsq');", '@import url(javascript:"iczpbtsq");'])
		js_vectors.extend(["x {x:expression('iczpbtsq')}", 'x {x:expression("iczpbtsq")}'])
		js_vectors.extend(["x {background-image:url(javascript:'iczpbtsq')}", 'x {background-image:url(javascript:"iczpbtsq")}'])
		
		url_special_payloads = list(set(url_special_payloads))
		jsurl_special_payloads = list(set(jsurl_special_payloads))
		js_special_payloads = list(set(js_special_payloads))
		
		for spl_payload in jsurl_special_payloads:
			current_payload = spl_payload.replace("<url>", "javascript:'iczpbtsq'")
			current_payload = self.InsertCssQuotes(quote, current_payload)
			if self.IsCssPayloadAllowed(InStyleAttribute, current_payload):
				self.InjectAndCheckCss(current_payload, "iczpbtsq", "js")
			current_payload = spl_payload.replace("<url>", 'javascript:"iczpbtsq"')
			current_payload = self.InsertCssQuotes(quote, current_payload)
			if self.IsCssPayloadAllowed(InStyleAttribute, current_payload):
				self.InjectAndCheckCss(current_payload, "iczpbtsq", "js")
		
		for spl_payload in js_special_payloads:
			current_payload = spl_payload.replace("<js>", "iczpbtsq")
			current_payload = self.InsertCssQuotes(quote, current_payload)
			if self.IsCssPayloadAllowed(InStyleAttribute, current_payload):
				self.InjectAndCheckCss(current_payload, "iczpbtsq", "js")
		
		for spl_payload in url_special_payloads:
			current_payload = spl_payload.replace("<url>", "//iczpbtsq")
			current_payload = self.InsertCssQuotes(quote, current_payload)
			if self.IsCssPayloadAllowed(InStyleAttribute, current_payload):
				self.InjectAndCheckCss(current_payload, "//iczpbtsq", "url")

		
		for vector in url_vectors:
			current_payload = payload.replace("<vector>", vector)
			current_payload = self.InsertCssQuotes(quote, current_payload)
			if self.IsCssPayloadAllowed(InStyleAttribute, current_payload):
				self.InjectAndCheckCss(current_payload, "//iczpbtsq", "url")
		for vector in js_vectors:
			current_payload = payload.replace("<vector>", vector)
			current_payload = self.InsertCssQuotes(quote, current_payload)
			if self.IsCssPayloadAllowed(InStyleAttribute, current_payload):
				self.InjectAndCheckCss(current_payload, "iczpbtsq", "js")
		
	def IsCssPayloadAllowed(self, InStyleAttribute, payload):
		if payload.count("{") > 0 or payload.count("}") > 0:
			if InStyleAttribute:
				return False
		return True
	
	def InjectAndCheckCss(self, payload, keyword, url_or_js):
		self.Scnr.RequestTrace("Injecting {0} - ".format(payload))
		res = self.Scnr.Inject(payload)
		if self.IsReqCssContext(res, keyword, url_or_js):
			self.Scnr.ResponseTrace("<i<cr>>XSS inside CSS successful!<i</cr>>")
			self.AddToTriggers(payload, keyword)
			self.SetConfidence(3)
		else:
			self.Scnr.ResponseTrace("Not in interesting CSS context")
	
	
	def IsReqCssContext(self, res, keyword, url_or_js):
		contexts = self.GetCssContexts(keyword, res)
		for context in contexts:
			context_parts = context.split("-")
		
			if context_parts[0] == "Value":
				if context_parts[1] == "JS":
					if url_or_js == "js":
						return True
				elif context_parts[1] == "Url":
					if url_or_js == "url":
						return True
			elif context_parts[0] == "Import":
				if context_parts[1] == "Raw" or context_parts[1] == "Url":
					if context_parts[2] == "Start" or context_parts[2] == "Full":
						if url_or_js == "url":
							return True
				elif context_parts[1] == "RawJS" or context_parts[1] == "UrlJS":
					if url_or_js == "js":
						return True
		return False
	
	def InsertCssQuotes(self, quote, payload):
		if quote == "Double":
			return payload.replace("<quote>",'"')
		elif  quote == "Single":
			return payload.replace("<quote>","'")
		else:
			return payload.replace("<quote>","")
	
	def CheckForCrossSiteCookieSetting(self):
		meta_set_cookies = self.ps_res.Html.GetMetaContent("http-equiv", "set-cookie")
		header_set_cookies = []
		if self.ps_res.Headers.Has("Set-Cookie"):
			header_set_cookies = self.ps_res.Headers.GetAll("Set-Cookie")
		
		meta_csc = False
		header_csc = False
		
		for i in range(2):
			if i ==0:
				set_cookies = meta_set_cookies
			else:
				set_cookies = header_set_cookies
			for set_cookie in set_cookies:
				if set_cookie.lower().count(self.ps) > 0:
					if i == 0:
						meta_csc = True
						self.Scnr.Trace("<i<br>><i<cr>>Injected ProbeString '{0}' is reflected inside Set-Cookie HTTP-EQUIV Meta Tag. Allows Cross-site Cookie Setting!<i</cr>>".format(self.ps))
					else:
						header_csc = True
						self.Scnr.Trace("<i<br>><i<cr>>Injected ProbeString '{0}' is reflected inside Set-Cookie Header. Allows Cross-site Cookie Setting!<i</cr>>".format(self.ps))
				break
		if meta_csc or header_csc:
			self.ReportCrossSiteCookieSetting(meta_csc, header_csc)
			
	def CheckCharsetSecurity(self):
		
		if not self.base_res.IsCharsetSet:
			self.ReportCharsetNotSet()
			
		self.Scnr.Trace("<i<br>><i<h>>Checking for Charset Manipulation:<i</h>>")
		
		charsets = ["UTF-8", "UTF-7"]
		inj_req = []
		inj_res = []
		payloads = []
		match_count = 0
		for charset in charsets:
			self.Scnr.RequestTrace("  Injected {0} - ".format(charset))
			res = self.Scnr.Inject(charset)
			inj_req.append(self.Scnr.InjectedRequest)
			inj_res.append(res)
			payloads.append(charset)
			if res.BodyEncoding == charset:
				match_count = match_count + 1
				self.Scnr.ResponseTrace("<i<b>>Response Charset matches injected value - {0}<i</b>>".format(charset))
			else:
				self.Scnr.ResponseTrace("Response Charset is {0} and does not match the injected value".format(res.BodyEncoding))
		if match_count == 2:
			self.Scnr.Trace("<i<cr>>It is possible to manipulate the response Charset!!<i</cr>>")
			self.ReportCharsetManipulation(inj_req, inj_res, payloads)
		else:
			self.Scnr.Trace("Charset manipulation was not successful")
	
	#css,js,html,attributes,attribute,unknown
	def GetContext(self, InjectedValue, Res):
		contexts_list = []
		if Res.Headers.Has("Refresh"):
			refresh_header = Res.Headers.Get("Refresh").strip()
			rh_parts = refresh_header.split(";", 1)
			if len(rh_parts) == 2:
				rh_url = rh_parts[1].lower().strip().lstrip("url=").strip().strip("'").strip('"')
				if rh_url.count(InjectedValue.lower()) > 0:
					contexts_list.append("UrlAttribute")
		if(Res.IsHtml):
			contexts_list.extend(Res.Html.GetContext(InjectedValue))
		elif(Res.IsCss):
			contexts_list.append("CSS")
		elif(Res.IsJavaScript or Res.IsJson):
			contexts_list.append("JS")
		else:
			contexts_list.append("Unknown")
		return contexts_list
	
	
	def ReportCSSTestLead(self):
		PR = PluginResult(self.Scnr.InjectedRequest.Host)
		PR.Title = "XSS Plugin found reflection in CSS"
		PR.Summary = "Data injected in to the '{0}' parameter of the {1} is being reflected back as part of CSS. Manually check this for XSS.".format(self.Scnr.InjectedParameter, self.Scnr.InjectedSection)
		PR.Triggers.Add("", self.Scnr.InjectedRequest, "", self.Scnr.InjectionResponse)
		PR.ResultType = PluginResultType.TestLead
		self.Scnr.AddResult(PR)
	
	def ReportJSTestLead(self):
		PR = PluginResult(self.Scnr.InjectedRequest.Host)
		PR.Title = "XSS Plugin found reflection in JavaScript"
		PR.Summary = "Data injected in to the '{0}' parameter of the {1} is being reflected back inside JavaScript. Manually check this for XSS.".format(self.Scnr.InjectedParameter, self.Scnr.InjectedSection)
		PR.Triggers.Add("", self.Scnr.InjectedRequest, "", self.Scnr.InjectionResponse)
		PR.ResultType = PluginResultType.TestLead
		self.Scnr.AddResult(PR)
		
	def AddToTriggers(self, RequestTrigger, ResponseTrigger):
		self.RequestTriggers.append(RequestTrigger)
		self.ResponseTriggers.append(ResponseTrigger)
		self.TriggerRequests.append(self.Scnr.InjectedRequest.GetClone())
		self.TriggerResponses.append(self.Scnr.InjectionResponse.GetClone())
		
	def AddToTriggersWithProbeStringInjection(self, RequestTrigger, ResponseTrigger):
		self.RequestTriggers.append(RequestTrigger)
		self.ResponseTriggers.append(ResponseTrigger)
		self.TriggerRequests.append(self.ps_req)
		self.TriggerResponses.append(self.ps_res)
		
	def SetConfidence(self, NewConfidence):
		if NewConfidence > self.Confidence:
			self.Confidence = NewConfidence
	
	def CheckResponseDetails(self, res):
		if self.Scnr.InjectedSection == "URL" and self.ps_res.Code == 404:
			return
		if self.ps_res.Code != res.Code:
			self.Scnr.SetTraceTitle("Injection Response Code varies from baseline", 2)
		elif self.ps_res.BodyLength + res.BodyLength > 0:
			diff_percent = (res.BodyLength * 1.0)/((self.ps_res.BodyLength + res.BodyLength)* 1.0)
			if(diff_percent > 0.6 or  diff_percent < 0.4):
				self.Scnr.SetTraceTitle("Injection Response Length varies from baseline", 1)
	
	def ReportInjectionInSpecialAttributes(self, payload):
		all_tags_and_attrs = []
		for i in range(len(self.injectable_special_tags)):
			all_tags_and_attrs.append("    {0}) <i<b>>{1}<i</b>> attribute of <i<b>>{2}<i</b>> tag".format(i + 1, self.injectable_special_tags[i], self.injectable_special_attributes[i]))
		PR = PluginResult(self.Scnr.InjectedRequest.Host)
		PR.Title = "Scriptless HTML Injection"
		PR.Summary = "Scriptless HTML Injection has been detected in the '{0}' parameter of the {1} section of the request.<i<br>>It is possible to inject a remote URL in to the following sensitive HTML attributes:<i<br>>{2}  <i<br>><i<br>><i<hh>>Test Trace:<i</hh>>{3}".format(self.Scnr.InjectedParameter, self.Scnr.InjectedSection, "<i<br>>".join(all_tags_and_attrs), self.Scnr.GetTrace())
		PR.Triggers.Add(payload, self.Scnr.InjectedRequest, payload, self.Scnr.InjectionResponse)
		PR.Severity = PluginResultSeverity.High
		PR.Confidence = PluginResultConfidence.High
		self.Scnr.SetTraceTitle("Scriptless HTML Injection Found", 100)
		self.Scnr.AddResult(PR)
	
	def ReportCrossSiteCookieSetting(self, meta_csc, header_csc):
		PR = PluginResult(self.Scnr.InjectedRequest.Host)
		PR.Title = "Cross-site Cookie Setting"
		if meta_csc and header_csc:
			context = "META HTTP-EQUIV Set-Cookie tag and Set-Cookie header"
		elif meta_csc:
			context = "META HTTP-EQUIV Set-Cookie tag"
		else:
			context = "Set-Cookie header"
		PR.Summary = "Cross-site Cookie Setting has been detected in the '{0}' parameter of the {1} section of the request. The value of this parameter is return in the {2}".format(self.Scnr.InjectedParameter, self.Scnr.InjectedSection, context)
		PR.Triggers.Add(self.ps, self.ps_req, self.ps, self.ps_res)
		PR.Severity = PluginResultSeverity.Medium
		PR.Confidence = PluginResultConfidence.Medium
		self.Scnr.SetTraceTitle("Cross-site Cookie Setting", 50)
		self.Scnr.AddResult(PR)
	
	def ReportCharsetNotSet(self):
		PR = PluginResult(self.Scnr.InjectedRequest.Host)
		PR.Title = "Charset Not Set By Server"
		PR.Summary = "The Charset of the response content is not explicitly set by the server. Lack of charset can cause the browser to guess the encoding type and this could lead to Cross-site Scripting by encoding the payload in encoding types like UTF-7."
		PR.Triggers.Add("", self.base_req, "", self.base_res)
		PR.Severity = PluginResultSeverity.Medium
		PR.Confidence = PluginResultConfidence.Medium
		self.Scnr.SetTraceTitle("Charset Missing", 50)
		self.Scnr.AddResult(PR)
	
	def ReportCharsetManipulation(self, inj_req, inj_res, payloads):
		PR = PluginResult(self.Scnr.InjectedRequest.Host)
		PR.Title = "Charset Manipulation Possible"
		PR.Summary = "Charset Manipulation Possible has been detected in the '{0}' parameter of the {1} section of the request.<i<br>>It is possible to set the charset of the response body to any desired encoding type.<i<br>><i<br>><i<hh>>Test Trace:<i</hh>>{2}".format(self.Scnr.InjectedParameter, self.Scnr.InjectedSection, self.Scnr.GetTrace())
		for i in range(len(payloads)):
			PR.Triggers.Add(payloads[i], inj_req[i], payloads[i], inj_res[i])
		PR.Severity = PluginResultSeverity.Medium
		PR.Confidence = PluginResultConfidence.High
		self.Scnr.SetTraceTitle("Charset Manipulation", 50)
		self.Scnr.AddResult(PR)
	
	def ReportSameSiteScriptInclude(self, scripts_vuln, styles_vuln):
		PR = PluginResult(self.Scnr.InjectedRequest.Host)
		all_vuln = []
		all_vuln.extend(scripts_vuln)
		all_vuln.extend(styles_vuln)
		scope = ""
		if len(scripts_vuln) > 0 and len(styles_vuln) > 0:
			scope = "JS and CSS"
		elif len(scripts_vuln) > 0:
			scope = "JS"
		else:
			scope = "CSS"
		PR.Title = "In-domain {0} Inclusion".format(scope)
		PR.Summary = "In-domain {0} Inclusion has been detected in the '{1}' parameter of the {2} section of the request.<i<br>>It is possible to set the location of {3} source URL to a resource within the same domain. If user's are allowed to upload text files on to this domain then an attacker can upload script as a regular text file and execute it using this vulnerability.<i<br>><i<br>><i<hh>>Test Trace:<i</hh>>{4}".format(scope, self.Scnr.InjectedParameter, self.Scnr.InjectedSection, scope, self.Scnr.GetTrace())
		PR.Triggers.Add(self.ps, self.ps_req, "\r\n".join(all_vuln), self.ps_res)
		PR.Severity = PluginResultSeverity.Medium
		PR.Confidence = PluginResultConfidence.High
		self.Scnr.SetTraceTitle("In-domain {0} Inclusion".format(scope), 50)
		self.Scnr.AddResult(PR)
	
	def AnalyseResults(self):
		if(len(self.RequestTriggers) > 0):
			PR = PluginResult(self.Scnr.InjectedRequest.Host)
			PR.Title = "Cross-site Scripting Detected"
			PR.Summary = "Cross-site Scripting has been detected in the '{0}' parameter of the {1} section of the request  <i<br>><i<br>><i<hh>>Test Trace:<i</hh>>{2}".format(self.Scnr.InjectedParameter, self.Scnr.InjectedSection, self.Scnr.GetTrace())
			for i in range(len(self.RequestTriggers)):
				PR.Triggers.Add(self.RequestTriggers[i], self.TriggerRequests[i], self.ResponseTriggers[i], self.TriggerResponses[i])
			PR.ResultType = PluginResultType.Vulnerability
			PR.Severity = PluginResultSeverity.High
			if self.Confidence == 3:
				PR.Confidence = PluginResultConfidence.High
			elif self.Confidence == 2:
				PR.Confidence = PluginResultConfidence.Medium
			else:
				PR.Confidence = PluginResultConfidence.Low
			self.Scnr.AddResult(PR)
			self.Scnr.SetTraceTitle("XSS Found", 100)
		
		self.Scnr.LogTrace()

p = CrossSiteScripting()
ActivePlugin.Add(p.GetInstance())
