package gov.nist.spectrumbrowser.common;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.Response;
import com.google.gwt.http.client.URL;
import com.google.gwt.user.client.Window;

public abstract class AbstractSpectrumBrowserService {
	protected String baseUrl;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	
	class MyCallback implements RequestCallback {
		public SpectrumBrowserCallback<String> callback;

		public MyCallback(SpectrumBrowserCallback<String> callback) {
			this.callback = callback;
		}

		@Override
		public void onResponseReceived(Request request, Response response) {
			int status = response.getStatusCode();
			if (status == 200) {
				callback.onSuccess(response.getText());
			} else {
				callback.onFailure(new Exception("Error response " + status));
			}
		}

		@Override
		public void onError(Request request, Throwable exception) {
			callback.onFailure(exception);
		}

	}
	


	protected void dispatch(String uri, SpectrumBrowserCallback<String> callback) {
		try {
			String rawUrl = baseUrl + uri;
			String url = URL.encode(rawUrl);
			logger.finer("URL = " + url);
			RequestBuilder requestBuilder = new RequestBuilder(
					RequestBuilder.POST, url);
			requestBuilder.setCallback(new MyCallback(callback));
			requestBuilder.send();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, " Error contacting server", ex);
		}
	}
	
	protected void dispatchWithJsonContent(String uri, String requestData, SpectrumBrowserCallback<String> callback) {
		try {
			String rawUrl = baseUrl + uri;
			String url = URL.encode(rawUrl);
			logger.finer("URL = " + url);
			if(url.toLowerCase().contains("authenticate") || url.toLowerCase().contains("account")
					|| url.toLowerCase().contains("password"))
			{
			}
			else
			{
				//only log json data if not account info:
				logger.finer("requestData = " + requestData);
			}
			RequestBuilder requestBuilder = new RequestBuilder(
					RequestBuilder.POST, url);
			requestBuilder.setHeader("Content-Type", "application/json");
			requestBuilder.setRequestData(requestData);
			requestBuilder.setCallback(new MyCallback(callback));
			requestBuilder.send();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, " Error contacting server", ex);
		}
	}
	
	protected void dispatchWithJsonContent(String baseUrl, String uri, String requestData, SpectrumBrowserCallback<String> callback) {
		try {
			String rawUrl = baseUrl + uri;
			String url = URL.encode(rawUrl);
			logger.finer("URL = " + url);
			if(url.toLowerCase().contains("authenticate") || url.toLowerCase().contains("account")
					|| url.toLowerCase().contains("password"))
			{
			}
			else
			{
				//only log json data if not account info:
				logger.finer("requestData = " + requestData);
			}
			RequestBuilder requestBuilder = new RequestBuilder(
					RequestBuilder.POST, url);
			requestBuilder.setHeader("Content-Type", "application/json");
			requestBuilder.setRequestData(requestData);
			requestBuilder.setCallback(new MyCallback(callback));
			requestBuilder.send();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, " Error contacting server", ex);
		}
	}
	
	
	protected void dispatch(String baseUrl, String uri, SpectrumBrowserCallback<String> callback){
		try {
			String rawUrl = baseUrl + uri;
			String url = URL.encode(rawUrl);
			logger.finer("URL = " + url);
			RequestBuilder requestBuilder = new RequestBuilder(
					RequestBuilder.POST, url);
			requestBuilder.setCallback(new MyCallback(callback));
			requestBuilder.send();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, " Error contacting server", ex);
		}
	}
	
	public void authenticate(String jsonContent, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {


		dispatchWithJsonContent("authenticate", jsonContent, callback);

	}
	
	public void logOut(String sessionId,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String uri = "logOut/" + sessionId;
		dispatch(uri, callback);
	}
	

}
