package gov.nist.spectrumbrowser.client;

import com.google.gwt.http.client.RequestException;


public interface SpectrumBrowserServiceAsync {
	/**
	 * Unprivileged login a user given user name.
	 * Returns an authentcation token (sessionId) to be used in all subsequent interactions.
	 * 
	 * 
	 * @param name -- user name
	 * @return --- a json string containing the session id.
	 * @throws RequestException 
	 */
	void authenticate(
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	/**
	 * Authenticates a user given user name and password.
	 * Returns an authentcation token (sessionId) to be used in all subsequent interactions.
	 * 
	 * 
	 * @param name -- user name
	 * @param password -- user password.
	 * @return --- a json string containing the session id.
	 */
	void authenticate(String userName, String password, String privilege,
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	/**
	 * log out and destroy all tokens for this login.
	 * 
	 * @param sessionId -- session ID.
	 */
	
	void logOut(String sessionId, SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	/**
	 * Gets the location names for which data is available.
	 * 
	 * @param sessionId - session id returned by authentication
	 * @return a json string containing the location names.
	 * @throws IllegalArgumentException
	 */
	
	
	void getAdminBand(String sessionId, String bandName, SpectrumBrowserCallback<String> SpectrumBrowserCallback)throws IllegalArgumentException;
	
	
	void getLocationInfo(String sessionId, SpectrumBrowserCallback<String> SpectrumBrowserCallback)throws IllegalArgumentException;
	
	/**
	 * Gets the record count (number of scans) for a given location between the given time limits.
	 * 
	 * @param sessionId -- session id for the authenticated session
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

	void getDataSummary(String sessionId, String sensorId,  double lat, double lng, double alt, long minTime,
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

	void getPowerVsTimeAndSpectrum(String sessionId, String location, long time,
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

	
	void  generateDailyStatistics(String sessionId, String location, long minDate,
			long minFreq, long maxFreq, int minPower, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException;
	
	/**
	 * generate the daily statistics and return them for plotting.
	 * @param maxFreq 
	 * @param mSubBandMaxFreq 
	 * @param mSubBandMinFreq 
	 * 
	 */
	void getDailyMaxMinMeanStats(String sessionId, String sensorId, 
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
	void getOneDayStats(String sessionId, String sensorId, long startTime,
			String sys2detect, long minFreq, long maxFreq, 
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	/**
	 * Log a message to the server.
	 * 
	 * @param logMessage -- the message to log.
	 */
	void log(String logMessage);

	/**
	 * Generate a single acuqisition spectrogram at the default cutoff.
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param mSelectionTime
	 * @param mMaxFreq 
	 * @param mMinFreq 
	 */
	void generateSingleAcquisitionSpectrogramAndOccupancy(String sessionId, String sensorId,
			long mSelectionTime, String sys2detect, long mMinFreq, long mMaxFreq, 
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;

	/**
	 * Generate a single acquistion spectrogram at the specified cutoff.
	 * @param sessionId - session ID for current login.
	 * @param mSensorId - sensor ID
	 * @param mSelectionTime - selection time.
	 * @param maxFreq - max Freq of the acquisition.
	 * @param minFreq - min freq of the acquisition.
	 * @param callback -- the callback.
	 */
	void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sessionId, String mSensorId, long selectionTime,
			String sys2detect, long minFreq, long maxFreq, int cutoff, SpectrumBrowserCallback<String> callback);
	
	/**
	 * 
	 * @param sessionId - session ID of current login.
	 * @param sensorId - sensor ID
	 * @param selectionTime - time of acquisiton.
	 * @param minFreq - min freq of acquisiton.
	 * @param maxFreq - max freq of acquisition.
	 * @param leftBoundary - left boundary of time window ( milliseconds)
	 * @param rightBoundary - right boundary of time window (milliseconds)
	 * @param cutoff
	 * @param callback
	 */
	void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sessionId, String sensorId, long selectionTime,
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
	void generateSpectrum(String sessionId, String sensorId, long startTime, long milisecondOffset,
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
	void generateSpectrum(String sessionId, String sensorId, long startTime, long milisecondOffset,
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
	void generatePowerVsTime(String sessionId, String sensorId, long startTime, long freq,
			SpectrumBrowserCallback<String> callback);
	
	/**
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param startTime
	 * @param freq
	 * @param callback
	 */
	void generatePowerVsTime(String sessionId, String sensorId, long startTime, long freq, int leftBound, 
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
			String sessionId,
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
			String sessionId,
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
	 * Generate a file for dowload and return a URL to the file.
	 * 
	 * @param sensorId
	 * @param tSelectedStartTime
	 * @param dayCount
	 * @param callback
	 */
	void generateZipFileForDownload(String sessionId, String sensorId, long tSelectedStartTime,
			int dayCount, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback);

	/**
	 * Email the URL for generated file to the user.
	 * 
	 * @param sessionId
	 * @param uriPrefix
	 * @param uri
	 * @param emailAddress
	 * @param callback
	 */
	void emailUrlToUser(String sessionId,
			String uriPrefix, String uri, 
			String emailAddress, SpectrumBrowserCallback<String> callback);
	
	/**
	 * Check for dump availability.
	 * 
	 * @param sessionId -- session ID.
	 * @param uri -- URI to check for the dump (the last part of the URL).
	 * @param callback -- the call back to call on response from the server.
	 */
	void emailChangePasswordUrlToUser(String sessionId,
			String uriPrefix, 
			String emailAddress, SpectrumBrowserCallback<String> callback);
	
	
	
	void checkForDumpAvailability(String sessionId, String uri, SpectrumBrowserCallback<String> callback);
	
	/**
	 * Get the last acquisition time.
	 * @param sessionId
	 * @param sensorId
	 * @param maxFreq 
	 * @param minFreq 
	 */
	void getLastAcquisitionTime(String sessionId, String sensorId,  String sys2Detect, long minFreq, long maxFreq, SpectrumBrowserCallback<String> callback);

	/**
	 * Get the count of acquistions in an interval.
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
	void getAcquisitionCount(String id, String sys2Detect, long minFreq,
			long maxFreq, long selectedStartTime, int dayCount,
			String sessionId,
			SpectrumBrowserCallback<String> spectrumBrowserCallback);
}
