package gov.nist.spectrumbrowser.client;

import java.util.Date;
import java.util.HashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.i18n.client.DateTimeFormat;
import com.google.gwt.i18n.client.DateTimeFormat.PredefinedFormat;
import com.google.gwt.i18n.client.TimeZone;
import com.google.gwt.i18n.client.constants.TimeZoneConstants;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TabBar;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.datepicker.client.DatePicker;
import com.smartgwt.client.widgets.toolbar.ToolStrip;
import com.smartgwt.client.widgets.toolbar.ToolStripButton;


public class SpectrumLocationSelection extends Composite {

	private static final long MILISEC_PER_DAY = 24 * 60 * 60 * 1000;
	static Logger logger = Logger.getLogger("SpectrumBrowser");

	private final VerticalPanel verticalPanel;

	private String locationSelection;
	private long absMinDate;
	private long absMaxDate;
	private long minDate;
	private long maxDate;
	private int readingsCount;

	// Information retrieved from the server.
	private HashMap<String, Long[]> minMaxTimes = new HashMap<String, Long[]>();
	private HashMap<String, Long[]> minMaxFreqs = new HashMap<String, Long[]>();
	private HashMap<String, Integer[]> minMaxPower = new HashMap<String, Integer[]>();
	private JSONObject timeZonesMap;
	private HashMap<String,TimeZone> timeZones = new HashMap<String,TimeZone>();
	private JSONObject timesMap;
	private JSONObject powerMap;
	private JSONObject freqMap;
	private JSONObject readingsCountMap;
	private JSONArray locationArray;

	// GUI elements.
	private VerticalPanel startDatePanel;
	private VerticalPanel endDatePanel;
	private VerticalPanel readingsPanel;
	private DatePicker startDate;
	private DatePicker endDate;
	private Label startDateLabel;
	private Label endDateLabel;
	private Label readingCountLabel;
	// private TextBox decimationLabel;
	private TextBox minFrequencyLabel;
	private TextBox maxFrequencyLabel;
	private ListBox locationSelector;

	private final SpectrumBrowser spectrumBrowser;
	private String sessionId;
	DialogBox helpBox ;
	
	

	class LocationClickHandler implements ClickHandler {

		private JSONArray locationArray;
		private ListBox locationList;

		public LocationClickHandler(JSONArray locationArray,
				ListBox locationList) {
			this.locationArray = locationArray;
			this.locationList = locationList;
		}

		@Override
		public void onClick(ClickEvent clickEvent) {
			int locationIndex = locationList.getSelectedIndex();
			locationSelection = locationArray.get(locationIndex).isString()
					.stringValue();
			logger.fine("Location = " + locationSelection);
			minDate = getUtcTime(minMaxTimes.get(locationSelection)[0]);
			maxDate = getUtcTime(minMaxTimes.get(locationSelection)[1]);
			readingsCount = Integer.parseInt(readingsCountMap
					.get(locationSelection).isString().stringValue());
			update();
		}

	}

	private TimeZone getTimeZone() {
		return timeZones.get(locationSelection);		
	}

	// Note that all date values are normalized to universal date before
	// we see them.
	public String formatDate(long time) {
		Date newValue = new Date(getTimeZoneOffset(time));
		return DateTimeFormat.getFormat(PredefinedFormat.DATE_SHORT).format(
				newValue);
	}

	public String formatDateLong(long time) {
		
		Date newValue = new Date(getTimeZoneOffset(time));
		DateTimeFormat dateTimeFormat = DateTimeFormat.getFormat("yyyy-MM-dd HH:mm:ss");
		return dateTimeFormat.format(newValue,getTimeZone())+ " "+ getTimeZone().getID();
	}

	private void update() {
		startDate.setCurrentMonth(new Date(minDate));
		startDate.setValue(new Date(minDate));
		// startDateLabel.setText(formatDate(new Date(minDate)));
		endDate.setCurrentMonth(new Date(maxDate));
		endDate.setValue(new Date(maxDate));
		// endDateLabel.setText(formatDate(new Date(maxDate)));
		readingCountLabel.setText(Integer.toString(readingsCount));
	}
	
	public long getTimeZoneOffset(long time) {
		int offset = this.getTimeZone().getOffset(new Date(time));
		return time + offset*60*1000;
	}
	
	public long getUtcTime(long time) {
		int offset = this.getTimeZone().getOffset(new Date(time));
		logger.finer("Offset = " + offset);
		return time - offset*60*1000;
	}

	long roundDown(long time) {
		
		long tmin = (getTimeZoneOffset(time) / MILISEC_PER_DAY) * MILISEC_PER_DAY;
		try {
			if (tmin < absMinDate)
				tmin = absMinDate;

			return tmin;
		} finally {
			logger.finer("roundDown : " + time + " tmin " + tmin);

		}
	}

	long roundUp(long time) {
		long tmax = (getTimeZoneOffset(time) / MILISEC_PER_DAY) * MILISEC_PER_DAY;
	    tmax += MILISEC_PER_DAY;
		try {

			if (tmax > absMaxDate) {
				logger.finer("computed max date outside limit " + maxDate);
				tmax = absMaxDate;
			}

			return tmax;
		} finally {
			logger.finer("roundUp : " + time + " returning " + tmax);

		}

	}

	void getReadingsCount() {
	
	}

	/**
	 * Draw the screen.
	 */

	public void draw() {

		startDatePanel = new VerticalPanel();
		endDatePanel = new VerticalPanel();
		readingsPanel = new VerticalPanel();
		startDate = new DatePicker();
		endDate = new DatePicker();
		startDateLabel = new Label();
		endDateLabel = new Label();
		readingCountLabel = new Label();
		// decimationLabel = new TextBox();
		minFrequencyLabel = new TextBox();
		maxFrequencyLabel = new TextBox();
		locationSelector = new ListBox();
		ToolStrip toolStrip = new ToolStrip();
		ToolStripButton helpButton = new ToolStripButton("Help");
		toolStrip.addButton(helpButton);
		//helpButton.setBackgroundColor("#0000ff");
		verticalPanel.add(toolStrip);
		helpBox = new DialogBox();
	    Button ok = new Button("OK");
	     ok.addClickHandler(new ClickHandler() {
	        public void onClick(ClickEvent event) {
	          helpBox.hide();
	        }
	     });
	    helpBox.add(ok);
		helpButton.addClickHandler(new com.smartgwt.client.widgets.events.ClickHandler(){

			@Override
			public void onClick(
					com.smartgwt.client.widgets.events.ClickEvent event) {
				  helpBox.setText("Please select location and range of interest. \nClick on the Generate Spectrogram button");			     
				  helpBox.show();
				
			}});
		
		
		HTML title = new HTML(
				"<H1> Select location and range of interest </H1>", true);
		verticalPanel.add(title);

	
		SpectrumLocationSelection.this.verticalPanel.add(locationSelector);
		locationSelector.setTitle("Locations");
		locationSelector.setFocus(true);

		SpectrumLocationSelection.this.verticalPanel.add(locationSelector);

		locationSelector.setVisible(true);
		for (int i = 0; i < locationArray.size(); i++) {
			// For each location, get the min and max frequencies
			JSONString location = locationArray.get(i).isString();
			locationSelector.addItem(location.stringValue());

		}
		
		locationSelector.addClickHandler(new LocationClickHandler(
				locationArray, locationSelector));

		startDatePanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
		startDate.setTitle("Start Date");
		startDate.setCurrentMonth(new Date(minDate));
		startDate.setValue(new Date(minDate));
		startDate.addValueChangeHandler(new ValueChangeHandler<Date>() {

			@Override
			public void onValueChange(ValueChangeEvent<Date> vce) {
				Date newValue = vce.getValue();
				// go to the day boundry.
				long newMin = getUtcTime(newValue.getTime());
				if (newMin >= absMinDate && newMin <= maxDate) {
					minDate = newMin;
				}
				getReadingsCount();
				update();

			}
		});
		getReadingsCount();
		update();

		HTML html = new HTML("<b>Start Date</b>", true);
		startDateLabel.setText(formatDate(minDate));
		startDatePanel.add(startDate);
		startDatePanel.add(startDateLabel);
		startDatePanel.add(html);
		html.setStyleName("textLabelStyle");

		endDatePanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);

		endDate.setCurrentMonth(new Date(maxDate));
		endDate.setValue(new Date(maxDate));
		endDate.setTitle("End Date");
		endDateLabel.setText(formatDate(maxDate));
		endDateLabel.setVisible(true);
		endDatePanel.add(endDate);
		endDatePanel.add(endDateLabel);
		html = new HTML("<b>End Date</b>", true);
		html.setStyleName("textLabelStyle");
		endDatePanel.add(html);
		endDate.addValueChangeHandler(new ValueChangeHandler<Date>() {

			@Override
			public void onValueChange(ValueChangeEvent<Date> vce) {

				Date newValue = vce.getValue();
				long newTime = getUtcTime(newValue.getTime());
				if (newTime <= absMaxDate && newTime >= minDate) {
					maxDate = newTime <= absMaxDate ? newTime : absMaxDate;
				} else {
					logger.log(Level.FINER, "date set too high " + newTime
							+ " > " + absMaxDate);
				}
				getReadingsCount();
				update();

			}
		});

		readingsPanel.setWidth("400px");
		readingsPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);

		readingsCount = Integer.parseInt(readingsCountMap
				.get(locationSelection).isString().stringValue());
		readingCountLabel.setText(readingsCountMap.get(locationSelection)
				.isString().stringValue());
		readingCountLabel.setVisible(true);
		readingsPanel.add(readingCountLabel);
		html = new HTML("<b>Number of readings in date range. </b>");
		html.setStyleName("textLabelStyle");
		readingsPanel.add(html);

		// decimationLabel.setText("1");
		// html = new HTML("<b>Decimation for Spectrogram </b>");
		// html.setStyleName("textLabelStyle");
		// readingsPanel.add(decimationLabel);
		// readingsPanel.add(html);

		readingsPanel.add(minFrequencyLabel);
		html = new HTML(
				"<b>Min. Freq. to be included in Spectrogram (MHz). </b>");
		html.setStyleName("textLabelStyle");
		minFrequencyLabel.setText(Long.toString(minMaxFreqs
				.get(locationSelection)[0]));
		readingsPanel.add(minFrequencyLabel);
		readingsPanel.add(html);

		readingsPanel.add(maxFrequencyLabel);
		html = new HTML(
				"<b>Max. Freq. to be included in Spectrogram (MHz). </b>");
		html.setStyleName("textLabelStyle");
		maxFrequencyLabel.setText(Long.toString(minMaxFreqs
				.get(locationSelection)[1]));
		readingsPanel.add(maxFrequencyLabel);
		readingsPanel.add(html);

		ToolStripButton button = new ToolStripButton("Generate Spectrogram");
		button.setBorder("2px solid blue");
		
		button.addClickHandler(new com.smartgwt.client.widgets.events.ClickHandler() {

			@Override
			public void onClick(com.smartgwt.client.widgets.events.ClickEvent clickEvent) {
				try {
					long minFreq, maxFreq;
					try {
						minFreq = Long.parseLong(minFrequencyLabel.getText());
					} catch (NumberFormatException ex) {
						spectrumBrowser
								.displayError("Frequency Must be an integer.");
						return;
					}
					try {
						maxFreq = Long.parseLong(maxFrequencyLabel.getText());
					} catch (NumberFormatException ex) {
						spectrumBrowser
								.displayError("Frequency Must be an integer.");
						return;
					}

					if (minFreq > maxFreq) {
						spectrumBrowser
								.displayError("max frequency must be bigger than min frequency");
						return;
					}

					verticalPanel.clear();

					new Spectrogram(sessionId, spectrumBrowser,
							SpectrumLocationSelection.this, locationSelection,
							roundDown(minDate), roundUp(maxDate), absMinDate,
							absMaxDate, minFreq, maxFreq, verticalPanel);
				} catch (Exception ex) {
					logger.log(Level.SEVERE, "Error in creating spectrogram",
							ex);
				}

			}

			

		});

		toolStrip.addButton(button);
		
		ToolStripButton logoffButton = new ToolStripButton("Log off");
		toolStrip.addButton(logoffButton);
		logoffButton.setBorder("2px solid red");
		logoffButton.addClickHandler(new com.smartgwt.client.widgets.events.ClickHandler(){

			@Override
			public void onClick(
					com.smartgwt.client.widgets.events.ClickEvent event) {
				spectrumBrowser.logoff();
				
			}});
		HorizontalPanel selectionPanel = new HorizontalPanel();

		selectionPanel.add(startDatePanel);
		selectionPanel.add(readingsPanel);
		selectionPanel.add(endDatePanel);

		SpectrumLocationSelection.this.verticalPanel.add(selectionPanel);
		SpectrumLocationSelection.this.verticalPanel.setVisible(true);

	}

	/**
	 * Puts up a screen to allow the user to select the location.
	 * 
	 * @param sessionId
	 *            -- session ID from the login.
	 * @param spectrumBrowser
	 *            -- the service anchor
	 * @param verticalPanel
	 *            -- vertical panel on which we are attaching stuff.
	 */
	public SpectrumLocationSelection(String sessionId,
			SpectrumBrowser spectrumBrowser, VerticalPanel verticalPanel) {
		this.sessionId = sessionId;
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;

		// Get the location names and per location data.
	

		spectrumBrowser.getSpectrumBrowserService().getLocationInfo(sessionId,
				new SpectrumBrowserCallback<String>() {

					@Override
					public void onFailure(Throwable error) {
						logger.log(
								Level.SEVERE,
								"An error occured communicating with the server",
								error);
						SpectrumLocationSelection.this.spectrumBrowser
								.displayError("An Error occured communicating with the server");
					}

					@Override
					public void onSuccess(String result) {
						try {
							logger.fine("successfully retrieved location names" + result);
							/*JSONValue jsonValue = JSONParser
									.parseStrict(result);
							JSONObject jsonObject = jsonValue.isObject();
							locationArray = jsonObject.get("locations")
									.isArray();
							timesMap = jsonObject.get("maxMinTime").isObject();
							freqMap = jsonObject.get("maxMinFreqs").isObject();
							powerMap = jsonObject.get("minMaxPower").isObject();
							readingsCountMap = jsonObject.get("readingsCount")
									.isObject();
							timeZonesMap = jsonObject.get("timeZones")
									.isObject();
							for ( int i = 0; i <  locationArray.size(); i++){
								String loc = locationArray.get(i).isString().stringValue();
								int tzOffset = Integer.parseInt( timeZonesMap.get(loc).isString()
										.stringValue());
								logger.finer("TimeZoneOffset = " + tzOffset);	
								TimeZone tz = TimeZone.createTimeZone(tzOffset/(60*1000));
								timeZones.put(loc, tz);
							}
							for (int i = 0; i < locationArray.size(); i++) {
								// For each location, get the min and max frequencies
								JSONString location = locationArray.get(i).isString();
								//locationSelector.addItem(location.stringValue());

								// Get the minimum time in the range.
								JSONArray minMaxTime = timesMap.get(location.stringValue())
										.isArray();
								Long[] minMaxTimeValues = new Long[2];
								minMaxTimeValues[0] = Long.parseLong(minMaxTime.get(0).isString()
										.stringValue());
								minMaxTimeValues[1] = Long.parseLong(minMaxTime.get(1).isString()
										.stringValue());
								minMaxTimes.put(location.stringValue(), minMaxTimeValues);

								// Get the min and max frequencies in the range for the given
								// location.
								JSONArray minMaxFreq = freqMap.get(location.stringValue())
										.isArray();
								Long[] minMaxFrequencyValues = new Long[2];
								minMaxFrequencyValues[0] = Long.parseLong(minMaxFreq.get(0)
										.isString().stringValue());
								minMaxFrequencyValues[1] = Long.parseLong(minMaxFreq.get(1)
										.isString().stringValue());
								minMaxFreqs.put(location.stringValue(), minMaxFrequencyValues);

								// Get the min and max powers in the range for the given location.
								JSONArray minMaxPowers = powerMap.get(location.stringValue())
										.isArray();
								Integer[] minMaxPowerValues = new Integer[2];
								minMaxPowerValues[0] = Integer.parseInt(minMaxPowers.get(0)
										.isString().stringValue());
								minMaxPowerValues[1] = Integer.parseInt(minMaxPowers.get(1)
										.isString().stringValue());
								minMaxPower.put(location.stringValue(), minMaxPowerValues);

							}

							locationSelection = locationArray.get(0).isString().stringValue();
							minDate = getUtcTime((minMaxTimes.get(locationSelection)[0]));
							maxDate = getUtcTime((minMaxTimes.get(locationSelection)[1]));
							absMinDate = (minDate / MILISEC_PER_DAY) * MILISEC_PER_DAY;
							absMaxDate = (maxDate / MILISEC_PER_DAY) * MILISEC_PER_DAY + MILISEC_PER_DAY;
							
							
							SpectrumLocationSelection.this.draw(); */

						} catch (Exception ex) {
							logger.log(Level.SEVERE,
									"Error in retrieving values ", ex);
						}

					}
				});
		
	}

	public String getLocation() {
		return this.locationSelection;
	}

}
