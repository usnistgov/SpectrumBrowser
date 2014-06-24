package gov.nist.spectrumbrowser.client;


import java.util.logging.Handler;
import java.util.logging.LogRecord;

import com.google.gwt.dev.json.JsonString;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;

public class SpectrumBrowserLoggingHandler extends Handler {

	SpectrumBrowserServiceAsync spectrumBrowserService;

	public SpectrumBrowserLoggingHandler(SpectrumBrowserServiceAsync spectrumBrowserService) {
		this.spectrumBrowserService = spectrumBrowserService;
	}

	@Override
	public void publish(LogRecord record) {
		String message = record.getMessage();
		JSONObject jsonObject = new JSONObject();
		JSONValue jsonValue = new JSONString(message);
		jsonObject.put("message", jsonValue);
		JSONArray jsonArray = new JSONArray();
		Throwable thrown = record.getThrown();
		int j = 0;
		while (thrown != null) {
			JSONObject exceptionObject = new JSONObject();
			exceptionObject.put("ExceptionMessage", new JSONString(thrown.getMessage()));
			StackTraceElement[] stackTrace = thrown.getStackTrace();
			String messageToLog = "";
			for (int i = 0; i < stackTrace.length; i++) {
				String ste = stackTrace[i].getMethodName() + ":"
						+ stackTrace[i].getLineNumber();
				messageToLog += ste;
				messageToLog +="\n";
			}
			exceptionObject.put("StackTrace", new JSONString(messageToLog));
			jsonArray.set(j, exceptionObject);
			j++;
			thrown = thrown.getCause();
		}
		jsonObject.put("ExceptionInfo", jsonArray);
		
		spectrumBrowserService.log(jsonObject.toString());
	}

	@Override
	public void flush() {
		
	}

	@Override
	public void close() {
		
	}

}
