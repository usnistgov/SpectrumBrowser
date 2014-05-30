package gov.nist.spectrumbrowser.client;

import com.google.gwt.user.client.rpc.RemoteService;
import com.google.gwt.user.client.rpc.RemoteServiceRelativePath;

/**
 * The client side stub for the RPC service.
 */
public interface SpectrumBrowserService  {
	/**
	 * Authenticates a user given user name and password.
	 * Returns an authentcation token (sessionId) to be used in all subsequent interactions.
	 * 
	 * 
	 * @param name -- user name
	 * @param password -- user password.
	 * @return --- a json string containing the session id.
	 */
	public String authenticate(String name, String password) throws IllegalArgumentException;
	
	
	/**
	 * log out and destroy all tokens for this login.
	 * 
	 * @param sessionId -- session ID.
	 */
	public String logOut(String sessionId) throws IllegalArgumentException;
	
		
	/**
	 * Gets the location names for which data is available.
	 * 
	 * @param sessionId - session id returned by authentication
	 * @return a json string containing the location names.
	 * @throws IllegalArgumentException
	 */
	public String getLocationInfo(String sessionId) throws IllegalArgumentException;
	
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
	public int getRecordCount(String sessionId, String location, long minTime, long maxTime) throws IllegalArgumentException;
	
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
	public String getSpectrogramRegions(String sessionId,String location, long minDate, long maxDate,
			long minFreq, long maxFreq) throws IllegalArgumentException;
	

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
	
	public String getSpectrogram(String sessionId, 
			String location, long minDate, long maxDate,
			long minFreq, long maxFreq, int minPower,
			int maxPower) throws IllegalArgumentException;
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
	
	public String generateSpectrogram(String sessionId, 
			String location, long minDate, long maxDate,
			long minFreq, long maxFreq, int minPower,
			int maxPower) throws IllegalArgumentException;
	
	
	

	/**
	 * Generates the daily statistics for a given 24 hour period starting at the given minaTime
	 * @param sessionId
	 * @param location
	 * @param minDate
	 * @param minFreq
	 * @param maxFreq
	 * @param minPower
	 * @throws IllegalArgumentException
	 */
	String generateDailyStatistics(String sessionId, String location, long minDate,
		  long minFreq, long maxFreq,
		  int minPower ) throws IllegalArgumentException;
	
	/**
	 * Log a message to the server.
	 */
	void log (String message);
}
