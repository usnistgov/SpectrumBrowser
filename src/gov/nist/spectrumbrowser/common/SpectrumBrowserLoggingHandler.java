package gov.nist.spectrumbrowser.common;


import java.util.logging.Handler;
import java.util.logging.LogRecord;

import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.Response;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;

public class SpectrumBrowserLoggingHandler extends Handler {


	String loggingServiceUrl;
	
	public void log(String message, String url) {
		try {
			//String url = baseUrl + "log";
			if (AbstractSpectrumBrowser.getSessionToken() == null) {
				return;
			}
			String loggingUrl = url + "/" + AbstractSpectrumBrowser.getSessionToken();
			RequestBuilder requestBuilder = new RequestBuilder(
					RequestBuilder.POST, loggingUrl);
			requestBuilder.setRequestData(message);
			requestBuilder.setCallback(new RequestCallback() {

				@Override
				public void onResponseReceived(Request request,
						Response response) {
					// Ignore.
				}

				@Override
				public void onError(Request request, Throwable exception) {
					// TODO Auto-generated method stub

				}
			});
			requestBuilder.send();
		} catch (Throwable ex) {
			Window.alert("ERROR logging to server : " + ex.getMessage());
		}

	}
	public SpectrumBrowserLoggingHandler(String url) {
		this.loggingServiceUrl = url + "/log";
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
		String traceback = "";
		while (thrown != null) {
			thrown.fillInStackTrace();
			
			JSONObject exceptionObject = new JSONObject();
			exceptionObject.put("ExceptionMessage", new JSONString(thrown.getMessage()));
			StackTraceElement[] stackTrace = thrown.getStackTrace();
			String messageToLog = "";
			for (int i = 0; i < stackTrace.length; i++) {
				String ste = stackTrace[i].getMethodName() + ":"
						+ stackTrace[i].getLineNumber();
				messageToLog += ste;
				messageToLog +="\n";
				traceback += stackTrace[i] + "\n";
			}
			exceptionObject.put("StackTrace", new JSONString(messageToLog));
			jsonArray.set(j, exceptionObject);
			j++;
			thrown = thrown.getCause();
		}
		
		jsonObject.put("ExceptionInfo", jsonArray);
		if (!traceback.equals("")) {
			jsonObject.put("Traceback", new JSONString(traceback));
		}

		
		this.log(jsonObject.toString(),loggingServiceUrl);
	}

	@Override
	public void flush() {
		
	}

	@Override
	public void close() {
		
	}

}
