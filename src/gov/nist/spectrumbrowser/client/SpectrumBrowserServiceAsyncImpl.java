package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.net.URLEncoder;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.Response;
import com.google.gwt.http.client.URL;
import com.google.gwt.user.client.Window;

public class SpectrumBrowserServiceAsyncImpl 
		extends AbstractSpectrumBrowserService implements
		SpectrumBrowserServiceAsync  {
	
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	
	public SpectrumBrowserServiceAsyncImpl(String baseUrl) {
		this.baseUrl = baseUrl;
	}

	@Override
	public void authenticate(SpectrumBrowserCallback<String> callback) {
		String url = baseUrl;
		dispatch(url, callback);
	}

	


	
	@Override
	public void getLocationInfo(String sessionId,
			SpectrumBrowserCallback<String> callback) {
		logger.finer("getLocationInfo " + sessionId);
		String uri = "getLocationInfo/" + sessionId;
		dispatch(uri, callback);
	}

	@Override
	public void getDataSummary( String sensorId,double lat, double lng, double alt,
			 long minTime, int dayCount, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
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
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		dispatch(baseUrl,uri, callback);
	}

	
	@Override
	public void getPowerVsTimeAndSpectrum(String sensorId,
			long time, long freq, long minTime, long maxTime, long minFreq,
			long maxFreq, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "getPowerVsTimeAndSpectrum/" + sessionId + "/"
				+ sensorId + "/" + minTime + "/" + maxTime + "/" + minFreq
				+ "/" + maxFreq + "/" + time + "/" + freq;
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		dispatch(baseUrl,uri, callback);

	}

	@Override
	public void generateDailyStatistics(String sensorId,
			long minTime, long minFreq, long maxFreq, int minPower,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String url = "getPowerVsTimeAndSpectrum/" + sensorId + "/" + minTime
				+ "/" + minFreq + "/" + sessionId + "?minPower=" + minPower;
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		dispatch(baseUrl,url, callback);

	}

	@Override
	public void getDailyMaxMinMeanStats(String sensorId,
			long minDate, long dayCount, String sys2detect, long minFreq, long maxFreq,
			long subBandMinFreq, long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri;
		if (minFreq == subBandMinFreq && maxFreq == subBandMaxFreq) {
			uri = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
				+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
				+ sessionId;
		} else if ( minFreq == subBandMinFreq) {
			uri = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMaxFreq=" + subBandMaxFreq;
		} else if ( maxFreq == subBandMaxFreq) {
			uri = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq;
		} else {
			uri = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq + "&" 
					+ "subBandMaxFreq=" + subBandMaxFreq;
		}
		dispatch(baseUrl,uri, callback);

	}

	

	@Override
	public void getOneDayStats(String sensorId,
			long startTime, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);

		String uri = "getOneDayStats/" + sensorId + "/" + startTime + "/" +sys2detect + "/" +  minFreq + "/" + maxFreq + "/"
				+ sessionId;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sensorId, long acquisitionTime,
			String sys2Detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2Detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
		    String sensorId, long acquisitionTime,
			String sys2detect,
			long minFreq, long maxFreq,
			int cutoff, SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);

		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSingleAcquisitionSpectrogramAndOccupancy" + "/"
				+ sensorId + "/" + acquisitionTime +"/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId
				+ "?cutoff=" + cutoff;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSpectrum(String sensorId,
			long startTime, long timeOffset,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSpectrum/" + sensorId + "/" + startTime + "/"
				+ timeOffset + "/" + sessionId;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSpectrum(String sensorId,
			long startTime, long timeOffset, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSpectrum/" + sensorId + "/" + startTime + "/"
				+ timeOffset + "/" + sessionId + "?subBandMinFrequency=" + minFreq +
				"&subBandMaxFrequency=" + maxFreq;
		dispatch(baseUrl,uri, callback);
	}
	@Override
	public void generatePowerVsTime(String sensorId,
			long startTime, long freq, SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);

		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generatePowerVsTime/" + sensorId + "/" + startTime + "/"
				+ freq + "/" + sessionId;
		dispatch(baseUrl,uri, callback);

	}

	@Override
	public void generatePowerVsTime(String sensorId,
			long startTime, long freq, int leftBound, int rightBound,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generatePowerVsTime/" + sensorId + "/" + startTime + "/"
				+ freq + "/" + sessionId + "?leftBound=" + leftBound
				+ "&rightBound=" + rightBound;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sensorId, long acquisitionTime,
			String sys2detect, long minFreq, long maxFreq,
			int leftBound, int rightBound, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2detect + "/" + minFreq + "/"
				+ maxFreq + "/" + sessionId
				+ "?cutoff=" + cutoff + "&leftBound=" + leftBound
				+ "&rightBound=" + rightBound;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleDaySpectrogramAndOccupancy(
			String sensorId,
			long acquistionTime,
			String sys2detect,
			long minFreq,
			long maxFreq,
			long subBandMinFreq,
			long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" + acquistionTime + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/" + sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq=" + subBandMaxFreq;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleDaySpectrogramAndOccupancy(
			String sensorId, long acquisitionTime, String sys2detect, long minFreq,
			long maxFreq, long subBandMinFreq, long subBandMaxFreq, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);

		String uri = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/" + sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq" + subBandMaxFreq+ "&cutoff=" + cutoff;
		dispatch(baseUrl,uri, callback);
		
	}

	

	@Override
	public void generateZipFileForDownload(String sensorId,
			long startTime, int dayCount, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generateZipFileFileForDownload"+  "/" + sensorId +"/" + startTime + "/" + dayCount + "/" +
			sys2detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(baseUrl,uri,callback);
	}

	@Override
	public void emailUrlToUser(
			String sensorId,
			String urlPrefix, String uri, 
			String emailAddress,SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String url = "emailDumpUrlToUser" + "/"  + emailAddress + "/" + sessionId +  "?urlPrefix=" + urlPrefix + "&uri=" + uri;
		dispatch(url,callback);
		
	}

	//mranga -- Does not need a session ID you have not logged in yet when you invoke this.
	@Override
	public void emailChangePasswordUrlToUser(String sessionId, 
			String urlPrefix, String emailAddress,SpectrumBrowserCallback<String> callback) {
		String url = "emailChangePasswordUrlToUser" + "/"  + emailAddress + "/" + sessionId +  "?urlPrefix=" + urlPrefix ;
		dispatch(url,callback);
		
	}
	
	@Override
	public void checkForDumpAvailability(String sensorId, String uri,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri2 = "checkForDumpAvailability/" + sessionId + "?uri=" + uri;
		dispatch(baseUrl,uri2,callback);
	}

	@Override
	public void getLastAcquisitionTime(String sensorId,
			String sys2Detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String url = "getLastAcquisitionTime/" + sensorId + "/" +sys2Detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(baseUrl,url,callback);
	}

	@Override
	public void getAcquisitionCount(String sensorId, String sys2Detect, long minFreq,
			long maxFreq, long selectedStartTime, int dayCount,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String url = "getAcquisitionCount/" + sensorId + "/" + sys2Detect + "/" + minFreq + "/" + maxFreq + "/" 
			+ selectedStartTime + "/" + dayCount + "/" + sessionId;
		dispatch(url,callback);
	}

	@Override
	public void createNewAccount(String firstName, String lastName,
			String emailAddress, String password,String urlPrefix, SpectrumBrowserCallback<String> callback) {

		String url = "createNewAccount/"+ emailAddress + "/" + password + "?firstName="+firstName + "&lastName="+lastName + "&urlPrefix="+urlPrefix;
		dispatch(url,callback);
	}

	@Override
	public void getLastAcquisitionTime(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String url = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "getLastSensorAcquisitionTimeStamp/" + sensorId + "/" + sessionId;
		dispatch (url,uri,callback);
		
	}
	
	
    @Override
	public void isAuthenticationRequired(
			SpectrumBrowserCallback<String> callback) {

		String uri = "isAuthenticationRequired";
		dispatch(uri,callback);
	}
    
    @Override
	public void isAuthenticationRequired(String url,
			SpectrumBrowserCallback<String> callback) {
		String uri = "/spectrumbrowser/isAuthenticationRequired";
		dispatch(url,uri,callback);
	}

	@Override
	public void logOff(SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionToken();
		super.logOut(sessionId, callback);
		
	}


}
