package gov.nist.spectrumbrowser.client;

import java.net.URLEncoder;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.Response;
import com.google.gwt.http.client.URL;
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
			String rawUrl = baseUrl + uri;
			String url = URL.encode(rawUrl);
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

		String uri = "authenticate/" + privilege + "/" + userName
				+ "?password=" + password;

		dispatch(uri, callback);

	}

	@Override
	public void logOut(String sessionId,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String uri = "logOut/" + sessionId;
		dispatch(uri, callback);
	}

	@Override
	public void getLocationInfo(String sessionId,
			SpectrumBrowserCallback<String> callback) {
		logger.finer("getLocationInfo " + sessionId);
		String uri = "getLocationInfo/" + sessionId;
		dispatch(uri, callback);
	}

	@Override
	public void getDataSummary(String sessionId, String sensorId,double lat, double lng, double alt,
			 long minTime, int dayCount, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String uri;
		if (minTime >= 0 && dayCount > 0) {
			uri = "getDataSummary/" + sensorId + "/" + lat + "/" + lng + "/" + alt + "/"
					+ sessionId + "?minTime=" + minTime + "&dayCount="
					+ dayCount + "&minFreq=" + minFreq + "&maxFreq=" + maxFreq;
		} else if (minTime > 0) {
			uri = "getDataSummary/" + sensorId + "/" + lat + "/" + lng + "/" + alt + "/"
					+ sessionId + "?minTime=" + minTime + "&minFreq="+ minFreq + "&maxFreq=" + maxFreq;
		} else {
			uri = "getDataSummary/" + sensorId + "/" + lat + "/" + lng + "/" + alt + "/"
					+ sessionId;
		}
		dispatch(uri, callback);
	}

	@Override
	public void generateSpectrogram(String sessionId, String dataSetName,
			long minDate, long maxDate, long minFreq, long maxFreq,
			int minPower, int maxPower, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String uri = "generateSpectrogram/" + sessionId + "/" + dataSetName
				+ "/" + minDate + "/" + maxDate + "/" + minFreq + "/" + maxFreq
				+ "?minPower=" + minPower + "&maxPower=" + maxPower;
		dispatch(uri, callback);

	}

	@Override
	public void getPowerVsTimeAndSpectrum(String sessionId, String dataSetName,
			long time, long freq, long minTime, long maxTime, long minFreq,
			long maxFreq, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url = "getPowerVsTimeAndSpectrum/" + sessionId + "/"
				+ dataSetName + "/" + minTime + "/" + maxTime + "/" + minFreq
				+ "/" + maxFreq + "/" + time + "/" + freq;
		dispatch(url, callback);

	}

	@Override
	public void generateDailyStatistics(String sessionId, String dataSetName,
			long minTime, long minFreq, long maxFreq, int minPower,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url = "getPowerVsTimeAndSpectrum/" + dataSetName + "/" + minTime
				+ "/" + minFreq + "/" + sessionId + "?minPower=" + minPower;
		dispatch(url, callback);

	}

	@Override
	public void getDailyMaxMinMeanStats(String sessionId, String sensorId,
			long minDate, long dayCount, long minFreq, long maxFreq,
			long subBandMinFreq, long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url;
		if (minFreq == subBandMinFreq && maxFreq == subBandMaxFreq) {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
				+ "/" + dayCount + "/" + minFreq + "/" + maxFreq + "/"
				+ sessionId;
		} else if ( minFreq == subBandMinFreq) {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMaxFreq=" + subBandMaxFreq;
		} else if ( maxFreq == subBandMaxFreq) {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq;
		} else {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq + "&" 
					+ "subBandMaxFreq=" + subBandMaxFreq;
		}
		dispatch(url, callback);

	}

	@Override
	public void log(String message) {
		try {
			String url = baseUrl + "log";
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

				}
			});
			requestBuilder.send();
		} catch (Exception ex) {
			Window.alert("ERROR logging to server : " + ex.getMessage());
		}

	}

	@Override
	public void getOneDayStats(String sessionId, String sensorId,
			long startTime, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url = "getOneDayStats/" + sensorId + "/" + startTime + "/" + minFreq + "/" + maxFreq + "/"
				+ sessionId;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sessionId, String sensorId, long acquisitionTime,
			long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sessionId, String sensorId, long acquisitionTime,
			long minFreq, long maxFreq,
			int cutoff, SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndOccupancy" + "/"
				+ sensorId + "/" + acquisitionTime +"/" + minFreq + "/" + maxFreq + "/" + sessionId
				+ "?cutoff=" + cutoff;
		dispatch(url, callback);
	}

	@Override
	public void generateSpectrum(String sessionId, String sensorId,
			long startTime, long timeOffset,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSpectrum/" + sensorId + "/" + startTime + "/"
				+ timeOffset + "/" + sessionId;
		dispatch(url, callback);
	}

	@Override
	public void generateSpectrum(String sessionId, String sensorId,
			long startTime, long timeOffset, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSpectrum/" + sensorId + "/" + startTime + "/"
				+ timeOffset + "/" + sessionId + "?subBandMinFrequency=" + minFreq +
				"&subBandMaxFrequency=" + maxFreq;
		dispatch(url, callback);
	}
	@Override
	public void generatePowerVsTime(String sessionId, String sensorId,
			long startTime, long freq, SpectrumBrowserCallback<String> callback) {
		String url = "generatePowerVsTime/" + sensorId + "/" + startTime + "/"
				+ freq + "/" + sessionId;
		dispatch(url, callback);

	}

	@Override
	public void generatePowerVsTime(String sessionId, String sensorId,
			long startTime, long freq, int leftBound, int rightBound,
			SpectrumBrowserCallback<String> callback) {
		String url = "generatePowerVsTime/" + sensorId + "/" + startTime + "/"
				+ freq + "/" + sessionId + "?leftBound=" + leftBound
				+ "&rightBound=" + rightBound;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sessionId, String sensorId, long acquisitionTime,
			long minFreq, long maxFreq,
			int leftBound, int rightBound, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + minFreq + "/"
				+ maxFreq + "/" + sessionId
				+ "?cutoff=" + cutoff + "&leftBound=" + leftBound
				+ "&rightBound=" + rightBound;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleDaySpectrogramAndOccupancy(
			String sessionId,
			String sensorId,
			long acquistionTime,
			long minFreq,
			long maxFreq,
			long subBandMinFreq,
			long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" + acquistionTime + "/" + minFreq + "/" + maxFreq + "/" + sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq" + subBandMaxFreq;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleDaySpectrogramAndOccupancy(String sessionId,
			String sensorId, long acquisitionTime, long minFreq,
			long maxFreq, long subBandMinFreq, long subBandMaxFreq, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + minFreq + "/" + maxFreq + "/" + sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq" + subBandMaxFreq+ "&cutoff=" + cutoff;
		dispatch(url, callback);
		
	}

	

	@Override
	public void generateZipFileForDownload(String sessionId, String sensorId,
			long startTime, int dayCount, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateZipFileFileForDownload"+  "/" + sensorId +"/" + startTime + "/" + dayCount +
				"/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(url,callback);
	}

	@Override
	public void emailUrlToUser(String sessionId, String urlPrefix, String uri, String emailAddress,SpectrumBrowserCallback<String> callback) {
		String url = "emailDumpUrlToUser" + "/"  + emailAddress + "/" + sessionId +  "?urlPrefix=" + urlPrefix + "&uri=" + uri;
		dispatch(url,callback);
		
	}

	@Override
	public void checkForDumpAvailability(String sessionId, String uri,
			SpectrumBrowserCallback<String> callback) {
		String url = "checkForDumpAvailability/" + sessionId + "?uri=" + uri;
		dispatch(url,callback);
	}

	@Override
	public void getLastAcquisitionTime(String sessionId, String sensorId,
			long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "getLastAcquisitionTime/" + sensorId + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(url,callback);
	}

	

}
