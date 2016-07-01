/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.common;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.VerticalPanel;

public abstract class AbstractSpectrumBrowserWidget extends Composite {

	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	protected VerticalPanel verticalPanel;
	
	
	
	protected float round(double val) {
		return (float) ((int) ((val + .0005) * 1000) / 1000.0);
	}

	public AbstractSpectrumBrowserWidget() {
		try {
			verticalPanel = new VerticalPanel();
			verticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			initWidget(verticalPanel);
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Problem initializing widget ", ex);
		}
	}

	protected String getAsString(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return jsonObject.get(keyName).isString().stringValue();
		} else {
			return "UNDEFINED";
		}

	}

	protected int getAsInt(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return (int) jsonObject.get(keyName).isNumber().doubleValue();
		} else {
			return 0;
		}
	}

	protected long getAsLong(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return (long) jsonObject.get(keyName).isNumber().doubleValue();
		} else {
			return 0;
		}
	}

	protected boolean getAsBoolean(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return jsonObject.get(keyName).isBoolean().booleanValue();
		} else {
			return false;
		}
	}

	public float getAsFloat(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return round(jsonObject.get(keyName).isNumber().doubleValue());
		} else {
			return 0;
		}
	}
}
