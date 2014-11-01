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
			long minDate, long dayCount, String sys2detect, long minFreq, long maxFreq,
			long subBandMinFreq, long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url;
		if (minFreq == subBandMinFreq && maxFreq == subBandMaxFreq) {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
				+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
				+ sessionId;
		} else if ( minFreq == subBandMinFreq) {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMaxFreq=" + subBandMaxFreq;
		} else if ( maxFreq == subBandMaxFreq) {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq;
		} else {
			url = "getDailyMaxMinMeanStats/" + sensorId + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq + "&" 
					+ "subBandMaxFreq=" + subBandMaxFreq;
		}
		dispatch(url, callback);

	}

	

	@Override
	public void getOneDayStats(String sessionId, String sensorId,
			long startTime, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String url = "getOneDayStats/" + sensorId + "/" + startTime + "/" +sys2detect + "/" +  minFreq + "/" + maxFreq + "/"
				+ sessionId;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sessionId, String sensorId, long acquisitionTime,
			String sys2Detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2Detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sessionId, String sensorId, long acquisitionTime,
			String sys2detect,
			long minFreq, long maxFreq,
			int cutoff, SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndOccupancy" + "/"
				+ sensorId + "/" + acquisitionTime +"/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId
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
			String sys2detect, long minFreq, long maxFreq,
			int leftBound, int rightBound, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2detect + "/" + minFreq + "/"
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
			String sys2detect,
			long minFreq,
			long maxFreq,
			long subBandMinFreq,
			long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" + acquistionTime + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/" + sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq=" + subBandMaxFreq;
		dispatch(url, callback);
	}

	@Override
	public void generateSingleDaySpectrogramAndOccupancy(String sessionId,
			String sensorId, long acquisitionTime, String sys2detect, long minFreq,
			long maxFreq, long subBandMinFreq, long subBandMaxFreq, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/" + sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq" + subBandMaxFreq+ "&cutoff=" + cutoff;
		dispatch(url, callback);
		
	}

	

	@Override
	public void generateZipFileForDownload(String sessionId, String sensorId,
			long startTime, int dayCount, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "generateZipFileFileForDownload"+  "/" + sensorId +"/" + startTime + "/" + dayCount + "/" +
			sys2detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(url,callback);
	}

	@Override
	public void emailUrlToUser(String sessionId, String urlPrefix, String uri, String emailAddress,SpectrumBrowserCallback<String> callback) {
		String url = "emailDumpUrlToUser" + "/"  + emailAddress + "/" + sessionId +  "?urlPrefix=" + urlPrefix + "&uri=" + uri;
		dispatch(url,callback);
		
	}

	// mranga - this will never be invoked by the browser. Does not need to be a service.
	@Override
	public void emailChangePasswordUrlToUser(String sessionId, String urlPrefix, String emailAddress,SpectrumBrowserCallback<String> callback) {
		String url = "emailChangePasswordUrlToUser" + "/"  + emailAddress + "/" + sessionId +  "?urlPrefix=" + urlPrefix ;
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
			String sys2Detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String url = "getLastAcquisitionTime/" + sensorId + "/" +sys2Detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(url,callback);
	}

	@Override
	public void getAcquisitionCount(String sensorId, String sys2Detect, long minFreq,
			long maxFreq, long selectedStartTime, int dayCount,
			String sessionId,
			SpectrumBrowserCallback<String> callback) {
		String url = "getAcquisitionCount/" + sensorId + "/" + sys2Detect + "/" + minFreq + "/" + maxFreq + "/" 
			+ selectedStartTime + "/" + dayCount + "/" + sessionId;
		dispatch(url,callback);
	}

	@Override
	public void createNewAccount(String firstName, String lastName,
			String emailAddress, String password, SpectrumBrowserCallback<String> callback) {

		String url = "createNewAccount/"+ emailAddress + "/" + password + "?firstName=\""+firstName + "\"&lastName=\""+lastName + "\"";
		dispatch(url,callback);
	}
	
	

	

}
