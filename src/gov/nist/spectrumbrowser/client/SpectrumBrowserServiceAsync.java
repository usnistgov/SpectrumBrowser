
package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;

import com.google.gwt.http.client.RequestException;


public interface SpectrumBrowserServiceAsync {
	
	
	/**
	 * Authenticates a user given user name and password.
	 * Returns an authentcation token (sessionId) to be used in all subsequent interactions.
	 * 
	 * 
	 * @param name -- user name
	 * @param password -- user password.
	 * @return --- a json string containing the session id.
	 */
	void authenticate(String jsonContent,
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	
	
	
	void getLocationInfo(String sessionId, SpectrumBrowserCallback<String> SpectrumBrowserCallback)throws IllegalArgumentException;
	
	/**
	 * Gets the record count (number of scans) for a given location between the given time limits.
	 * 
	 * @param lat -- location lat
	 * @param lng -- location longitude
	 * @param alt -- location altitude
	 * @param minTime -- min time ( ref jan 1 1970 miliseconds) of interval
	 * @param maxFreq 
	 * @param minFreq 
	 * @param maxTime -- max time of interval
	 * @return -- json formatted string containing the record count.
	 * @throws IllegalArgumentException
	 */

	void getDataSummary( String sensorId,  double lat, double lng, double alt, long minTime,
			int dayCount, long minFreq, long maxFreq, SpectrumBrowserCallback<String> SpectrumBrowserCallback) 
					throws IllegalArgumentException;
	
	
	
	
	/**
	 * Get the occupancy and spectrum data.
	 * 
	 * @param sessionId -- session id
	 * @param location -- location
	 * @param time -- time for the spectrum
	 * @param freq -- freq for the occupancy
	 * @param minFreq -- minFreq for the spectrum
	 * @param maxFreq -- maxFreq for the spectrum
	 * @param minTime -- min time for the occupancy chart.
	 * @param maxTime -- max time for the occupancy chart.
	 * @return -- json formatted string containing the 
	 * 				occupancy and spectrum.
	 * @throws IllegalArgumentException
	 */

	void getPowerVsTimeAndSpectrum( String sensorId, long time,
			long freq, long minTime, long maxTime, long minFreq, long maxFreq, 
		    SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	/**
	 * Get the occupancy and spectrum data.
	 * 
	 * @param sessionId -- session id
	 * @param location -- location
	 * @param time -- time for the spectrum
	 * @param freq -- freq for the occupancy
	 * @param minFreq -- minFreq for the spectrum
	 * @param maxFreq -- maxFreq for the spectrum
	 * @param minTime -- min time for the occupancy chart.
	 * @param maxTime -- max time for the occupancy chart.
	 * @return -- json formatted string containing the 
	 * 				occupancy and spectrum.
	 * @throws IllegalArgumentException
	 */

	
	void  generateDailyStatistics( String sensorId, long minDate,
			long minFreq, long maxFreq, int minPower, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException;
	
	/**
	 * generate the daily statistics and return them for plotting.
	 * @param maxFreq 
	 * @param mSubBandMaxFreq 
	 * @param mSubBandMinFreq 
	 * 
	 */
	void getDailyMaxMinMeanStats( String sensorId, 
			long minDate, long ndays,
			String sys2detect,
			long minFreq, long maxFreq, 
			long subBandMinFreq,
			long subBandMaxFreq, SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	/**
	 * Generate occupancy stats for a single day.
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param startTime - some time during the day for which data is needed.
	 * @param sys2detect
	 * @param maxFreq 
	 * @param minFreq 
	 * @param callback
	 * @throws IllegalArgumentException
	 */
	void getOneDayStats( String sensorId, long startTime,
			String sys2detect, long minFreq, long maxFreq, 
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	

	/**
	 * Generate a single acquisition spectrogram at the default cutoff.
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param mSelectionTime
	 * @param mMaxFreq 
	 * @param mMinFreq 
	 */
	void generateSingleAcquisitionSpectrogramAndOccupancy( String sensorId,
			long mSelectionTime, String sys2detect, long mMinFreq, long mMaxFreq, 
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;

	/**
	 * Generate a single acquisition spectrogram at the specified cutoff.
	 * @param sessionId - session ID for current login.
	 * @param mSensorId - sensor ID
	 * @param mSelectionTime - selection time.
	 * @param maxFreq - max Freq of the acquisition.
	 * @param minFreq - min freq of the acquisition.
	 * @param callback -- the callback.
	 */
	void generateSingleAcquisitionSpectrogramAndOccupancy(
		    String sensorId, long selectionTime,
			String sys2detect, long minFreq, long maxFreq, int cutoff, SpectrumBrowserCallback<String> callback);
	
	/**
	 * 
	 * @param sessionId - session ID of current login.
	 * @param sensorId - sensor ID
	 * @param selectionTime - time of acquisition.
	 * @param minFreq - min freq of acquisition.
	 * @param maxFreq - max freq of acquisition.
	 * @param leftBoundary - left boundary of time window ( milliseconds)
	 * @param rightBoundary - right boundary of time window (milliseconds)
	 * @param cutoff
	 * @param callback
	 */
	void generateSingleAcquisitionSpectrogramAndOccupancy(
		    String sensorId, long selectionTime,
			String sys2detect, long minFreq, long maxFreq,
			int leftBoundary, int rightBoundary,
			int cutoff, SpectrumBrowserCallback<String> callback);
	
	
	/**
	 * Generate spectrum for the entire band.
	 * @param sessionId
	 * @param sensorId
	 * @param startTime
	 * @param milisecondOffset
	 * @param callback
	 */
	void generateSpectrum( String sensorId, long startTime, long milisecondOffset,
			SpectrumBrowserCallback<String> callback);
	
	/**
	 * Generate the spectrum for a sub-band.
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param startTime
	 * @param milisecondOffset
	 * @param minFreq
	 * @param maxFreq
	 * @param callback
	 */
	void generateSpectrum(String sensorId, long startTime, long milisecondOffset,
			long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback);
	
	/**
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param startTime
	 * @param freq
	 * @param callback
	 */
	void generatePowerVsTime( String sensorId, long startTime, long freq,
			SpectrumBrowserCallback<String> callback);
	
	/**
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param startTime
	 * @param freq
	 * @param callback
	 */
	void generatePowerVsTime( String sensorId, long startTime, long freq, int leftBound, 
			int rightBound,
			SpectrumBrowserCallback<String> callback);
	
	/**
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param mSelectionTime
	 * @param mMinFreq
	 * @param mMaxFreq
	 * @param mSubBandMinFreq
	 * @param mSubBandMaxFreq
	 * @param spectrumBrowserCallback
	 */

	void generateSingleDaySpectrogramAndOccupancy(
			String sensorId,
			long mSelectionTime,
			String sys2detect,
			long mMinFreq,
			long mMaxFreq,
			long mSubBandMinFreq,
			long mSubBandMaxFreq,
			SpectrumBrowserCallback<String> spectrumBrowserCallback);
	
	/**
	 * 
	 * @param sessionId
	 * @param mSensorId
	 * @param nextAcquisitionTime
	 * @param minFreq
	 * @param maxFreq
	 * @param subBandMinFreq
	 * @param subBandMaxFreq
	 * @param cutoff
	 * @param spectrumBrowserCallback
	 */

	void generateSingleDaySpectrogramAndOccupancy(
			String mSensorId,
			long nextAcquisitionTime,
			String sys2detct,
			long minFreq,
			long maxFreq,
			long subBandMinFreq,
			long subBandMaxFreq,
			int cutoff,
			SpectrumBrowserCallback<String> spectrumBrowserCallback);

	
	/**
	 * Generate a file for download and return a URL to the file.
	 * 
	 * @param sensorId
	 * @param tSelectedStartTime
	 * @param dayCount
	 * @param callback
	 */
	void generateZipFileForDownload( String sensorId, long tSelectedStartTime,
			int dayCount, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback);
	
	/**
	 * View the capture events for this sensor.
	 * 
	 * @param sensorId
	 * @param sys2detect
	 * @param dayCount 
	 * @param startTime 
	 * @param callback
	 */
	void getCaptureEvents( String sensorId, String sys2dtect, long startTime, int dayCount, SpectrumBrowserCallback<String> callback);

	/**
	 * Email the URL for generated file to the user.
	 * 
	 * @param sessionId
	 * @param uriPrefix
	 * @param uri
	 * @param emailAddress
	 * @param callback
	 */
	void emailUrlToUser(
			String sensorId,
			String uri, 
			String emailAddress, SpectrumBrowserCallback<String> callback);
	
	/**
	 * Check for dump availability.
	 * 
	 * @param sessionId -- session ID.
	 * @param uri -- URI to check for the dump (the last part of the URL).
	 * @param callback -- the call back to call on response from the server.
	 */

	
	
	void checkForDumpAvailability( String sensorId, String uri, SpectrumBrowserCallback<String> callback);
	
	/**
	 * Get the last acquisition time.
	 * @param sessionId
	 * @param sensorId
	 * @param maxFreq 
	 * @param minFreq 
	 */
	void getLastAcquisitionTime( String sensorId,  String sys2Detect, long minFreq, long maxFreq, SpectrumBrowserCallback<String> callback);
	
	/**
	 * Get the last acquisition time for a given sensor.
	 * 
	 * @param sessionId
	 * @param sensorId
	 */
	void getLastAcquisitionTime( String sensorId, SpectrumBrowserCallback<String> callback);


	/**
	 * Get the count of acquisitions in an interval.
	 * 
	 * @param id
	 * @param sys2Detect
	 * @param minFreq
	 * @param maxFreq
	 * @param selectedStartTime
	 * @param dayCount
	 * @param sessionId
	 * @param spectrumBrowserCallback
	 */
	void getAcquisitionCount(String sensorId, String sys2Detect, long minFreq,
			long maxFreq, long selectedStartTime, int dayCount,
			SpectrumBrowserCallback<String> spectrumBrowserCallback);

	/**
	 * 
	 * @param firstName
	 * @param lastName
	 * @param emailAddress
	 * @param password
	 * @param urlPrefix
	 */
	void requestNewAccount(String jsonContent, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	/**
	 * 
	 * @param emailAddress
	 * @param oldPassword
	 * @param newPassword
	 * @param urlPrefix
	 */
	void changePassword(String jsonContent, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	/**
	 * 
	 * @param emailAddress
	 * @param password
	 * @param urlPrefix
	 */
	void requestNewPassword(String jsonContent, SpectrumBrowserCallback<String> spectrumBrowserCallback);

	
	/**
	 * Check whether authentication is required from our primary web service.
	 * @param callback
	 */
	
	void isAuthenticationRequired(
			SpectrumBrowserCallback<String> spectrumBrowserCallback);

	/**
	 * Check for authentication requirement from a peer.
	 * @param url
	 * @param spectrumBrowserCallback
	 */
	void isAuthenticationRequired(String url,
			SpectrumBrowserCallback<String> spectrumBrowserCallback);
	
	/**
	 * 
	 * @param spectrumBrowserCallback
	 */
	public void logOff(SpectrumBrowserCallback<String> spectrumBrowserCallback);
	
	/**
	 * @param spectrumBrowserCallback
	 */
	public void logOff(String sensorId,SpectrumBrowserCallback<String> spectrumBrowserCallback);

	public void getScreenConfig(SpectrumBrowserCallback<String> spectrumBrowserCallback);



	/**
	 * Session timeout check
	 * @param spectrumBrowserCallback
	 */
	void checkSessionTimeout(SpectrumBrowserCallback<String> spectrumBrowserCallback);
}
