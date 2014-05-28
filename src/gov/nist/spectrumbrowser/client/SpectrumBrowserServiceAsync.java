package gov.nist.spectrumbrowser.client;

import com.google.gwt.http.client.RequestException;


// Keep these in the same order as the SpectrumBrowserService! (why?)
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

	void getLocationInfo(String sessionId, SpectrumBrowserCallback<String> SpectrumBrowserCallback)throws IllegalArgumentException;
	
	/**
	 * Gets the record count (number of scans) for a given location between the given time limits.
	 * 
	 * @param sessionId -- session id for the authenticated session
	 * @param location -- location
	 * @param minTime -- min time ( ref jan 1 1970 miliseconds) of interval
	 * @param maxTime -- max time of interval
	 * @return -- json formatted string containing the record count.
	 * @throws IllegalArgumentException
	 */

	void getDataSummary(String sessionId, String sensorId,  String locationMessageId, long minTime,
			long maxTime, SpectrumBrowserCallback<String> SpectrumBrowserCallback) 
					throws IllegalArgumentException;
	
	/**
	 * Gets the bounding boxes for the available readings in a time and frequency window of interest.
	 * 
	 * @param sessionId -- authentication session id.
	 * @param location -- location for which the data is desired.
	 * @param minDate -- min time for which the data is desired.
	 * @param maxDate -- max time for which data is desired.
	 * @param minFreq -- min freq for which the data is desired
	 * @param maxFreq -- max freq for whcih the data is desired.
	 * @return a json string containing the bounding boxes.
	 * @throws IllegalArgumentException
	 */

	void getSpectrogramRegions(String sessionId, String location, long minDate,
			long maxDate, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	
	/**
	 * gets the spectrogram values in a given region 
	 * @param sessionId -- session id
	 * @param location -- location for which data is desired.
	 * @param minDate -- minimum date
	 * @param maxDate -- max date
	 * @param minFreq -- freq lower bound
	 * @param maxFreq -- max freq 
	 * @param minPower -- power lower bound
	 * @param maxPower -- power upper bound.
	 * @return - a comma separated list of values time,freq,power
	 *  for the spectrogram.
	 * @throws IllegalArgumentException
	 */
	
	void generateSpectrogram(String sessionId, String location, long minDate,
			long maxDate, long minFreq, long maxFreq, int minPower,
			int maxPower, SpectrumBrowserCallback<String> callback)
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
	 * 
	 */
	void getDailyMaxMinMeanStats(String sessionId, String sensorId, 
			long minDate, long ndays,
			SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;
	
	/**
	 * Generate occupancy stats for a single day.
	 * 
	 * @param sessionId
	 * @param sensorId
	 * @param startTime - some time during the day for which data is needed.
	 * @param callback
	 * @throws IllegalArgumentException
	 */
	void getOneDayStats(String sessionId, String sensorId, long startTime,
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
	 */
	void generateSingleAcquisitionSpectrogramAndPowerVsTimePlot(String sessionId, String sensorId,
			long mSelectionTime, SpectrumBrowserCallback<String> callback) throws IllegalArgumentException;

	/**
	 * Generate a single acquistion spectrogram at the specified cutoff.
	 * @param sessionId
	 * @param mSensorId
	 * @param mSelectionTime
	 * @param mTimeZoneId
	 * @param mWidth
	 * @param mHeight
	 * @param oneAcquisitionSpectrogramChart
	 */
	void generateSingleAcquisitionSpectrogramAndPowerVsTimePlot(
			String sessionId, String mSensorId, long mSelectionTime,
			int cutoff, SpectrumBrowserCallback<String> callback);
	
	/**
	 * Generate a spectrum for the given acquisiton at the given time offset.
	 */
	void generateSpectrum(String sessionId, String sensorId, long startTime, long milisecondOffset,
			SpectrumBrowserCallback<String> callback);

}
