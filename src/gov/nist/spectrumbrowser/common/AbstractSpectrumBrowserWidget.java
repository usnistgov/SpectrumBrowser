package gov.nist.spectrumbrowser.common;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Composite;
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
