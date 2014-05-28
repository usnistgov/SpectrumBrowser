package gov.nist.spectrumbrowser.client;

import java.util.logging.*;

import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.RequestException;
import com.google.gwt.http.client.Response;
import com.google.gwt.user.client.Window;


public class SpectrumBrowserServiceAsyncImpl implements
		SpectrumBrowserServiceAsync {

	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private String baseUrl;

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


	private void dispatch(String uri, SpectrumBrowserCallback<String> callback) {
		try {
			String url = baseUrl+ uri;
			RequestBuilder requestBuilder = new RequestBuilder(
					RequestBuilder.POST, url);
			logger.log(Level.FINER, "URL = " + url);
			requestBuilder.setCallback(new MyCallback(callback));
			requestBuilder.send();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error dispatching request", ex);
		}
	}

	public SpectrumBrowserServiceAsyncImpl(String baseUrl) {
		this.baseUrl = baseUrl;
	}

	@Override
	public void authenticate(SpectrumBrowserCallback<String> callback) {
		String url = baseUrl;
		dispatch(url, callback);
	}

	@Override
	public void authenticate(String userName, String password,
			String privilege, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {

		String uri =  "authenticate/" + privilege + "/" + userName
				+ "?password=" + password;

		dispatch(uri, callback);

	}

	@Override
	public void logOut(String sessionId, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String uri =  "logOut/" + sessionId;
		dispatch(uri, callback);
	}

	@Override
	public void getLocationInfo(String sessionId, SpectrumBrowserCallback<String> callback) {
		logger.finer("getLocationInfo " + sessionId);
		String uri = "getLocationInfo/" + sessionId;
		dispatch(uri, callback);
	}

	@Override
	public void getDataSummary(String sessionId, String sensorId, 
			String locationMessageId, long minTime, long maxTime, 
			SpectrumBrowserCallback<String> callback) {
		String uri;
		if ( minTime >= 0 && maxTime > 0) {
			uri = "getDataSummary/" + sensorId + "/" + locationMessageId + "/"
				+ sessionId + "?minTime=" + minTime + "&maxTime=" + maxTime ;
		} else if ( maxTime > 0) {
			uri = "getDataSummary/" + sensorId + "/" + locationMessageId + "/"
					+ sessionId + "?" +"maxTime=" + maxTime ;
		} else if (minTime > 0) {
			uri = "getDataSummary/" + sensorId + "/"  + locationMessageId + "/"
					+ sessionId + "?minTime=" + minTime ;
		} else {
			uri = "getDataSummary/" + sensorId + "/" +  locationMessageId + "/"
					+ sessionId;
		}
		dispatch(uri, callback);
	}
	
	

	@Override
	public void getSpectrogramRegions(String sessionId, String dataSetName,
			long minDate, long maxDate, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException {
		String uri = "getSpectrogramRegions/" + sessionId + "/"+ dataSetName + "/"
				+ minDate + "/" + maxDate + "/" + minFreq + "/" + maxFreq;
		dispatch(uri, callback);

	}

	@Override
	public void generateSpectrogram(String sessionId, String dataSetName,
			long minDate, long maxDate, long minFreq, long maxFreq,
			int minPower, int maxPower, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String uri = "generateSpectrogram/" + sessionId + "/"+ dataSetName + "/"
				+ minDate + "/" + maxDate + "/" + minFreq + "/" + maxFreq
				+ "?minPower=" + minPower + "&maxPower=" + maxPower ;
		dispatch(uri, callback);

	}

	@Override
	public void getPowerVsTimeAndSpectrum(String sessionId, String dataSetName,
			long time, long freq, long minTime, long maxTime, long minFreq,
			long maxFreq, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url = "getPowerVsTimeAndSpectrum/" + sessionId + "/" + dataSetName
				+ "/" + minTime + "/" + maxTime + "/" + minFreq + "/" + maxFreq
				+ "/" + time + "/" + freq ;
		dispatch(url, callback);

	}

	@Override
	public void generateDailyStatistics(String sessionId, String dataSetName,
			long minTime, long minFreq, long maxFreq, int minPower,
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException {
		String url = "getPowerVsTimeAndSpectrum/" + dataSetName
				+ "/" + minTime + "/" + minFreq + "/" + sessionId + "?minPower=" + minPower;
		dispatch(url, callback);

	}
	@Override
	public void getDailyMaxMinMeanStats(String sessionId, String sensorId,
			long minDate, long maxDate, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url = "getDailyMaxMinMeanStats/" + sensorId + "/"  + minDate + "/" + maxDate + "/" + sessionId  ;
		dispatch(url,callback);
		
	}

	@Override
	public void log(String message) {
		try {
			String url = baseUrl+ "log";
			RequestBuilder requestBuilder = new RequestBuilder(
					RequestBuilder.POST, url);
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
					
				}});
			requestBuilder.send();
		} catch (Exception ex) {
			Window.alert("ERROR logging to server : " + ex.getMessage());
		}
	
	}

	@Override
	public void getOneDayStats(String sessionId, String sensorId,
			 long startTime,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url = "getOneDayStats/" + sensorId + "/" + startTime + "/" + sessionId ;
		dispatch(url, callback);
	}
	
	@Override
	public void generateSingleAcquisitionSpectrogramAndPowerVsTimePlot(String sessionId, String sensorId, 
			long acquisitionTime, SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndPowerVsTimePlot/"+ sensorId + "/" 
			+ acquisitionTime + "/" + sessionId ;
		dispatch(url,callback);
	}
	@Override
	public void generateSingleAcquisitionSpectrogramAndPowerVsTimePlot(String sessionId, String sensorId, 
			long acquisitionTime, int cutoff, SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndPowerVsTimePlot/"+ sensorId + "/" 
			+ acquisitionTime + "/" + sessionId +"?cutoff=" + cutoff;
		dispatch(url,callback);
	}

	@Override
	public void generateSpectrum(String sessionId, String sensorId, long startTime,
			long milisecondOffset, SpectrumBrowserCallback<String> callback) {
		String url = "generateSpectrum/" + sensorId + "/" + startTime + "/" + milisecondOffset + "/" + sessionId;
		dispatch(url,callback);
	}

	
}
