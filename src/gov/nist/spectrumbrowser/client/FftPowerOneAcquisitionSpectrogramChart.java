package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserScreen;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.canvas.client.Canvas;
import com.google.gwt.core.client.Duration;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.dom.client.ImageElement;
import com.google.gwt.dom.client.Style.Cursor;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.ErrorEvent;
import com.google.gwt.event.dom.client.ErrorHandler;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.event.dom.client.MouseMoveEvent;
import com.google.gwt.event.dom.client.MouseMoveHandler;
import com.google.gwt.event.logical.shared.SelectionEvent;
import com.google.gwt.event.logical.shared.SelectionHandler;
import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TabPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.Selection;
import com.googlecode.gwt.charts.client.corechart.ScatterChart;
import com.googlecode.gwt.charts.client.corechart.ScatterChartOptions;
import com.googlecode.gwt.charts.client.event.HandlerRef;
import com.googlecode.gwt.charts.client.event.SelectEvent;
import com.googlecode.gwt.charts.client.event.SelectHandler;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.Legend;
import com.googlecode.gwt.charts.client.options.LegendPosition;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.kiouri.sliderbar.client.event.BarValueChangedEvent;
import com.kiouri.sliderbar.client.event.BarValueChangedHandler;
import com.kiouri.sliderbar.client.solution.simplevertical.SliderBarSimpleVertical;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class FftPowerOneAcquisitionSpectrogramChart extends
		AbstractSpectrumBrowserScreen implements
		SpectrumBrowserCallback<String> {

	private static final String COMPUTING_PLEASE_WAIT = "Computing Spectrogram. Please wait.";
	public static final String END_LABEL = "Acquisition Detail";
	String mSensorId;
	SpectrumBrowser mSpectrumBrowser;
	long mSelectionTime;
	SpectrumBrowserScreen mSpectrumBrowserShowDatasets;
	SpectrumBrowserScreen mDailyStatsChart;
	SpectrumBrowserScreen mOneDayOccupancyChart;
	JSONValue jsonValue;
	public static final long MILISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
	public float currentTime;
	public float currentFreq;
	private VerticalPanel spectrumAndOccupancyPanel;
	int cutoff;
	int maxPower;
	int cutoffPower;
	Label currentValue = new Label(
			"Click on spectrogram for power spectrum. Double click to zoom.");
	HorizontalPanel hpanel; // = new HorizontalPanel();
	VerticalPanel vpanel;// = new VerticalPanel();
	int spectrumCount;
	double minTime;
	double maxTime;
	double minFreqMhz;
	double maxFreqMhz;
	int timeDelta;
	private double yPixelsPerMegahertz;
	private int canvasPixelWidth;
	private int canvasPixelHeight;
	private Label maxPowerLabel;
	private Label minPowerLabel;
	private VerticalPanel spectrogramPanel;
	private VerticalPanel freqPanel;
	private HorizontalPanel powerMapPanel;
	private Canvas spectrogramCanvas;
	private HorizontalPanel xaxisPanel;
	private Image powerMapImage;
	private Image spectrogramImage;
	private String localDateOfAcquisition;
	private String cmapUrl;
	private String spectrogramUrl;
	private VerticalPanel occupancyPanel;
	private SliderBarSimpleVertical occupancyMinPowerSliderBar;
	private Label occupancyMinPowerLabel;
	private VerticalPanel occupancyMinPowerVpanel;
	private int minPower;
	private int noiseFloor;
	private int prevAcquisitionTime;
	private int nextAcquisitionTime;
	private ArrayList<Integer> timeArray;
	private ArrayList<Double> occupancyArray;
	private ScatterChart occupancyChart;
	private TabPanel tabPanel;
	private int zoom = 2;
	private int acquisitionDuration = 0;
	private int window;
	private int leftBound;
	private int rightBound;
	private Timer timer;
	private Grid commands;
	private long mMinFreq;
	private long mMaxFreq;
	private String mSys2detect;
	private HTML title;
	private ArrayList<SpectrumBrowserScreen> navigation;
	private int measurementsPerAcquisition;
	private int measurementsPerSecond;
	private Label help;
	private int measurementCount;
	private float maxOccupancy;
	private float minOccupancy;
	private float meanOccupancy;
	private float medianOccupancy;
	private int binsPerMesurement;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	/**
	 * Update the time and frequency readings on top of the plot if the user
	 * moves the mouse around in the canvas area.
	 *
	 */
	public class SurfaceMouseMoveHandlerImpl implements MouseMoveHandler {

		@Override
		public void onMouseMove(MouseMoveEvent event) {

			int timeCoord = event.getRelativeX(event.getRelativeElement());
			int freqCoord = event.getRelativeY(event.getRelativeElement());
			double xratio = ((double) timeCoord / (double) canvasPixelWidth);
			double yratio = 1.0 - ((double) freqCoord / (double) canvasPixelHeight);
			currentFreq = (float) (((maxFreqMhz - minFreqMhz) * yratio) + minFreqMhz);
			currentTime = (float) ((double) ((maxTime - minTime) * xratio) + minTime);
			currentValue.setText("MinTime = " + minTime + " Time (s) since acquistion start = "
					+ round2(currentTime) + "; Freq = " + currentFreq + " MHz");
		}

	}



	/*
	 * Callback for the selector that controls the cutoff power.
	 */
	public class OccupancyMinPowerSliderHandler implements
			BarValueChangedHandler {
		Label occupancyMinPowerLabel;

		public OccupancyMinPowerSliderHandler(Label occupancyMinPowerLabel) {
			occupancyMinPowerSliderBar.setValue(100);
			this.occupancyMinPowerLabel = occupancyMinPowerLabel;
			occupancyMinPowerLabel.setText(minPower + " dBm");
			this.occupancyMinPowerLabel
					.setTitle("Power Cutoff for Occupancy Graph");
		}

		@Override
		public void onBarValueChanged(BarValueChangedEvent event) {
			try {

				int occupancyBarValue = occupancyMinPowerSliderBar.getValue();
				logger.log(Level.FINEST, "bar value changed new value is "
						+ occupancyBarValue);
				cutoffPower = (int) ((1 - (double) occupancyBarValue / 100.0)
						* (maxPower - minPower) + minPower - 0.5);
				occupancyMinPowerLabel.setText(Integer
						.toString((int) cutoffPower) + " dBm");

			} catch (Exception ex) {
				logger.log(Level.SEVERE, " Exception ", ex);
			}

		}

	}

	public FftPowerOneAcquisitionSpectrogramChart(String sensorId,
			long selectionTime, String sys2detect, long minFreq, long maxFreq,
			VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser,
			ArrayList<SpectrumBrowserScreen> navigation) {


		logger.finer("FFtPowerOneAcquistionSpectrogramChart " + sensorId);
		mSys2detect = sys2detect;
		mSensorId = sensorId;
		mSelectionTime = selectionTime;
		mMinFreq = minFreq;
		mMaxFreq = maxFreq;
		minFreqMhz = mMinFreq / 1E6;
		maxFreqMhz = mMaxFreq / 1E6;
		vpanel = verticalPanel;
		mSpectrumBrowser = spectrumBrowser;
		super.setNavigation(verticalPanel, navigation, spectrumBrowser,
				END_LABEL);
		this.navigation = new ArrayList<SpectrumBrowserScreen>(navigation);
		this.navigation.add(this);
		mSpectrumBrowser.getSpectrumBrowserService()
				.generateSingleAcquisitionSpectrogramAndOccupancy(sensorId,
						mSelectionTime, mSys2detect, mMinFreq, mMaxFreq, this);

	}

	@Override
	public void onSuccess(String result) {
		try {
			Duration duration = new Duration();
			//logger.finer("result = " + result);
			jsonValue = JSONParser.parseLenient(result);
			if (!jsonValue.isObject().get(Defines.STATUS).isString().stringValue().equals("OK")) {
				Window.alert("Error : " + jsonValue.isObject().get(Defines.ERROR_MESSAGE).isString().stringValue());
				return;
			}
			timeDelta = (int)jsonValue.isObject().get("timeDelta").isNumber()
					.doubleValue();
			measurementsPerAcquisition = (int)jsonValue.isObject().get("measurementsPerAcquisition").isNumber().doubleValue();
			measurementCount = (int)jsonValue.isObject().get("measurementCount").isNumber().doubleValue();
			if (acquisitionDuration == 0) {
				leftBound = 0;
				rightBound = 0;
				acquisitionDuration = timeDelta;
				window = measurementsPerAcquisition;
				measurementsPerSecond = (int) (measurementsPerAcquisition/acquisitionDuration);

			}
			spectrogramUrl = jsonValue.isObject().get("spectrogram")
					.isString().stringValue();
			canvasPixelWidth = (int) jsonValue.isObject().get("image_width")
					.isNumber().doubleValue();
			canvasPixelHeight = (int) jsonValue.isObject().get("image_height")
					.isNumber().doubleValue();
			cmapUrl = jsonValue.isObject().get("cbar").isString()
					.stringValue();

			maxPower = (int) jsonValue.isObject().get("maxPower").isNumber()
					.doubleValue();
			cutoff = (int) ( jsonValue.isObject().get("cutoff").isNumber()
					.doubleValue());
			minPower = (int) jsonValue.isObject().get("minPower").isNumber()
					.doubleValue();
			noiseFloor = (int) jsonValue.isObject().get("noiseFloor")
					.isNumber().doubleValue();
			localDateOfAcquisition = jsonValue.isObject().get("formattedDate")
					.isString().stringValue();
			prevAcquisitionTime = (int) jsonValue.isObject()
					.get("prevAcquisition").isNumber().doubleValue();
			nextAcquisitionTime = (int) jsonValue.isObject()
					.get("nextAcquisition").isNumber().doubleValue();
			minTime = jsonValue.isObject().get("minTime").isNumber()
					.doubleValue();
			maxOccupancy = round2(jsonValue.isObject().get("maxOccupancy").isNumber().doubleValue()*100);
			minOccupancy = round2(jsonValue.isObject().get("minOccupancy").isNumber().doubleValue()*100);
			meanOccupancy = round2(jsonValue.isObject().get("meanOccupancy").isNumber().doubleValue()*100);
			medianOccupancy = round2(jsonValue.isObject().get("medianOccupancy").isNumber().doubleValue()*100);
			binsPerMesurement = (int) jsonValue.isObject().get("binsPerMeasurement").isNumber().doubleValue();
			maxTime = minTime + timeDelta;
			timeArray = new ArrayList<Integer>();
			occupancyArray = new ArrayList<Double>();
			int nvalues = jsonValue.isObject().get("timeArray").isArray()
					.size();
			for (int i = 0; i < nvalues; i++) {
				timeArray.add((int) jsonValue.isObject().get("timeArray")
						.isArray().get(i).isNumber().doubleValue());
				occupancyArray.add(jsonValue.isObject().get("occupancyArray")
						.isArray().get(i).isNumber().doubleValue());
			}
			long elapsedTime = duration.elapsedMillis();
			logger.finer("Unpacking json object took " + elapsedTime);

		} catch (Throwable throwable) {
			logger.log(Level.SEVERE, "Error parsing json result from server",
					throwable);
            logger.log(Level.SEVERE,"Offending json: "+result);
			mSpectrumBrowser.displayError("Error parsing JSON");
		}
		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);
		chartLoader.loadApi ( new Runnable() {

			@Override
			public void run() {
				draw();

			}});

	}

	private void zoomIn() {
		leftBound = (int)( (minTime  + (currentTime - minTime )
				/ (double) zoom)*1000);
		rightBound = (int) ((acquisitionDuration - maxTime) + (maxTime - currentTime)
				/ (double) zoom)*1000;
		window =  acquisitionDuration*1000 - leftBound - rightBound;
		logger.finer("mintTime " + minTime + " maxTime " + maxTime
				+ " currentTime " + currentTime + " leftBound " + leftBound
				+ " rightBound " + rightBound + " measurementsPerSecond = " + measurementsPerSecond);
		if (window < 50) {
			logger.finer("Max zoom reached " + window);
			return;
		}
		help.setText(COMPUTING_PLEASE_WAIT);
		mSpectrumBrowser.getSpectrumBrowserService()
				.generateSingleAcquisitionSpectrogramAndOccupancy(mSensorId,
						mSelectionTime, mSys2detect, mMinFreq, mMaxFreq,
						(int) leftBound, (int) rightBound, cutoff,
						FftPowerOneAcquisitionSpectrogramChart.this);
	}

	private void zoomOut() {
		if (maxTime - minTime < acquisitionDuration) {
			leftBound = 0;
			rightBound = 0;
			window = acquisitionDuration*1000;
			mSpectrumBrowser.getSpectrumBrowserService()
					.generateSingleAcquisitionSpectrogramAndOccupancy( mSensorId,
							mSelectionTime, mSys2detect, mMinFreq, mMaxFreq,
							FftPowerOneAcquisitionSpectrogramChart.this);
		}
	}

	/**
	 * This is called after the spectrogram has loaded from the server. Also
	 * gets called when we want to redraw the spectrogram.
	 *
	 */
	private void handleSpectrogramLoadEvent() {
		RootPanel.get().remove(spectrogramImage);

		spectrogramImage.setVisible(true);

		ImageElement imageElement = ImageElement.as(spectrogramImage
				.getElement());

		Canvas canvas = Canvas.createIfSupported();
		if (spectrogramCanvas != null) {
			spectrogramPanel.remove(spectrogramCanvas);
			spectrogramPanel.remove(xaxisPanel);
		}
		spectrogramCanvas = canvas;
		spectrogramCanvas.setCoordinateSpaceHeight(canvasPixelHeight);
		spectrogramCanvas.setCoordinateSpaceWidth(canvasPixelWidth);
		spectrogramCanvas
				.addMouseMoveHandler(new SurfaceMouseMoveHandlerImpl());

		canvas.getElement().getStyle().setCursor(Cursor.CROSSHAIR);

		spectrogramCanvas.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				if (timer == null) {
					timer = new Timer() {
						@Override
						public void run() {
							if (timer == null)
								return;
							logger.finer("OneAcquisitionSpegrogramChart: clickHandler");
							timer = null;
							if (currentFreq <= 0) {
								logger.finer("Freq is 0 -- doing nothing");
								return;
							}
						
							VerticalPanel powerVsTimeHpanel = new VerticalPanel();

							new PowerVsTime(mSpectrumBrowser,
									powerVsTimeHpanel, mSensorId,
									mSelectionTime, (long) (currentFreq * 1E6),
									canvasPixelWidth, canvasPixelHeight,
									leftBound, rightBound);
							new PowerSpectrum(mSpectrumBrowser,
									powerVsTimeHpanel, mSensorId,
									mSelectionTime, (long)(currentTime*Defines.MILISECONDS_PER_SECOND),
									canvasPixelWidth, canvasPixelHeight);
							tabPanel.add(powerVsTimeHpanel,
									Float.toString(round2(currentTime)) + " s");
						}
					};
					timer.schedule(300);
				} else {
					zoomIn();
					timer.cancel();
					timer = null;
				}

			}
		});

		spectrogramCanvas.getContext2d().drawImage(imageElement, 0, 0);
		spectrogramCanvas.getContext2d().rect(0, 0, canvasPixelWidth,
				canvasPixelHeight);
		spectrogramPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		spectrogramPanel.clear();
		spectrogramPanel.setHeight(canvasPixelHeight + "px");
		spectrogramPanel.add(spectrogramCanvas);
		spectrogramPanel.add(xaxisPanel);

		freqPanel.setHeight(canvasPixelHeight + "px");
		logger.log(Level.FINER, "Image Height " + canvasPixelHeight);

		yPixelsPerMegahertz = (double) (canvasPixelHeight)
				/ (double) (maxFreqMhz - minFreqMhz);
		logger.finer("yPixelsPerMegaherz = " + yPixelsPerMegahertz
				+ "canvasPixelHeight " + canvasPixelHeight);

		if (cmapUrl != null) {
			ImagePreloader.load(cmapUrl, new ImageLoadHandler() {

				@Override
				public void imageLoaded(ImageLoadEvent event) {
					Image image = new Image();
					image.setUrl(event.getImageUrl());
					image.setPixelSize(30, canvasPixelHeight);					
					image.setVisible(true);
					if (powerMapImage != null) {
						powerMapPanel.remove(powerMapImage);

					}
					powerMapPanel.add(image);
					powerMapImage = image;
					powerMapPanel.setHeight(canvasPixelHeight + "px");

				}
			});
		}

	}

	private void setSpectrogramImage() {
		try {

			spectrogramImage = new Image();
			// spectrogramImage.setWidth(canvasPixelWidth + "px");
			spectrogramImage.setPixelSize(canvasPixelWidth, canvasPixelHeight);
			// spectrogramImage.setFixedWidth(canvasPixelWidth);
			spectrogramImage.addLoadHandler(new LoadHandler() {

				@Override
				public void onLoad(LoadEvent event) {

					logger.fine("Image loaded");
					handleSpectrogramLoadEvent();

				}
			});
			spectrogramImage.setVisible(false);

			ImageElement imageElement = ImageElement.as(spectrogramImage
					.getElement());
			imageElement.setAttribute("HEIGHT", canvasPixelHeight + "px");
			spectrogramImage.setHeight(canvasPixelHeight + "px");

			logger.log(Level.FINER, "Setting URL " + spectrogramUrl);
			spectrogramImage.addErrorHandler(new ErrorHandler() {

				@Override
				public void onError(ErrorEvent event) {
					logger.log(Level.SEVERE, "Error loading image " +event.toDebugString());
					Window.alert("Error loading image");

				}
			});

			spectrogramImage.setUrl(spectrogramUrl);
			RootPanel.get().add(spectrogramImage);

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error retrieving image", ex);
		}
	}

	private void drawOccupancyChart() {
		final DataTable dataTable = DataTable.create();
		dataTable.addColumn(ColumnType.NUMBER);
				//" Time since start acquisition (s).");
		dataTable.addColumn(ColumnType.NUMBER); //, " Occupancy %");
		dataTable.addRows(timeArray.size());
		for (int i = 0; i < timeArray.size(); i++) {
			dataTable.setCell(i, 0, (double) timeArray.get(i)/1000,  "Time offset = " + (double) timeArray.get(i)/1000
					+ " s; Occupancy = " + round2( occupancyArray.get(i)*100) + " %");
			dataTable.setCell(i, 1, round2( occupancyArray.get(i)*100),"");
		}

		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

		chartLoader.loadApi(new Runnable() {

			@Override
			public void run() {
				occupancyChart = new ScatterChart();
				occupancyChart.setWidth(canvasPixelWidth + "px");
				occupancyChart.setHeight(canvasPixelHeight + "px");
				occupancyChart
						.setPixelSize(canvasPixelWidth, canvasPixelHeight);
				ScatterChartOptions options = ScatterChartOptions.create();
				options.setBackgroundColor("#f0f0f0");
				options.setPointSize(2);
				options.setWidth(canvasPixelWidth);
				options.setHeight(canvasPixelHeight);
				Legend legend = Legend.create();
				legend.setPosition(LegendPosition.NONE);
				options.setLegend(legend);
				options.setHAxis(HAxis
						.create("Time Since Start of Aquisition (s)"));
				options.setVAxis(VAxis.create("Occupancy %"));
				occupancyChart.setStyleName("lineChart");

				occupancyChart.draw(dataTable, options);
				occupancyChart.setVisible(true);
				occupancyPanel.add(occupancyChart);
			
				occupancyChart.addSelectHandler(new SelectHandler() {
					@Override
					public void onSelect(SelectEvent event) {
						if (timer != null && timer.isRunning()) {
							return;
						}
						timer = new Timer() {
							@Override
							public void run() {				
								JsArray<Selection> selection = occupancyChart
										.getSelection();
								if (selection == null) {
									return;
								}
								int row = selection.get(0).getRow();
								int delta = timeArray.get(row);
								logger.finer("OneAcquisitionSpegrogramChart: clickHandler");
								VerticalPanel spectrumHpanel = new VerticalPanel();
								new PowerSpectrum(mSpectrumBrowser,
										spectrumHpanel, mSensorId,
										mSelectionTime, (long)( delta),
										canvasPixelWidth, canvasPixelHeight);
								
								tabPanel.add(spectrumHpanel, Float.toString(round2((double)delta/1000.0))
										+ " s	");
							}};
						timer.schedule(500);
						
					}
				});

			}
		});

	}

	public void draw() {
		try {
			vpanel.clear();

			super.drawNavigation();
			HTML pageTitle = new HTML("<h2>" + getEndLabel() + "</h2>");
			vpanel.add(pageTitle);

			title = new HTML("<H3>Acquisition Start Time : "
					+ localDateOfAcquisition + "; Occupancy Threshold : "
					+ cutoff + " dBm; Noise Floor : " + noiseFloor
					+ "dBm.; Measurements Per Acquisition = " + measurementsPerAcquisition + "</H3>");

			vpanel.add(title);

			double timeResolution = timeDelta / measurementCount;

			int freqResolution = (int) round ((this.maxFreqMhz - this.minFreqMhz)/this.binsPerMesurement*measurementsPerAcquisition);

			HTML subTitle = new HTML("<h3>Time Resolution= " + round3(timeResolution)  +  " sec; Resolution BW = " + freqResolution + " kHz; Measurements = "
			+ measurementCount + "; Max Occupancy = " + maxOccupancy + "%; Median Occupancy = " + medianOccupancy + "%; Mean Occupancy = " + meanOccupancy +
			 "%; Min Occupancy = "+ minOccupancy+"%</h3>");
			vpanel.add(subTitle);


			help = new Label("Single click for detail. Double click to zoom");
			vpanel.add(help);

			VerticalPanel tab1Panel = new VerticalPanel();

			hpanel = new HorizontalPanel();

			commands = new Grid(1, 6);
			commands.setStyleName("selectionGrid");

			for (int i = 0; i < commands.getRowCount(); i++) {
				for (int j = 0; j < commands.getColumnCount(); j++) {
					commands.getCellFormatter().setHorizontalAlignment(i, j,
							HasHorizontalAlignment.ALIGN_CENTER);
					commands.getCellFormatter().setVerticalAlignment(i, j,
							HasVerticalAlignment.ALIGN_MIDDLE);
				}
			}

			hpanel.setSpacing(10);
			hpanel.setStyleName("spectrogram");
			xaxisPanel = new HorizontalPanel();
			xaxisPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			HorizontalPanel xaxis = new HorizontalPanel();
			xaxis.setWidth(canvasPixelWidth + 30 + "px");
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			NumberFormat numberFormat = NumberFormat.getFormat("00.00");
			xaxis.add(new Label(numberFormat.format(minTime)));
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			xaxis.add(new Label("Time (sec)"));
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			xaxis.add(new Label(numberFormat.format(minTime + timeDelta)));
			xaxisPanel.add(xaxis);

			// Attach the previous reading button.

			if (prevAcquisitionTime != mSelectionTime) {

				final Button prevDayButton = new Button();
				prevDayButton.setEnabled(true);
				prevDayButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						mSelectionTime = prevAcquisitionTime;
						prevDayButton.setEnabled(false);
						acquisitionDuration = 0;
						leftBound = 0;
						rightBound = 0;
						window = measurementsPerAcquisition;
						help.setText(COMPUTING_PLEASE_WAIT);
						mSpectrumBrowser
								.getSpectrumBrowserService()
								.generateSingleAcquisitionSpectrogramAndOccupancy(
										mSensorId,
										prevAcquisitionTime,
										mSys2detect,
										mMinFreq,
										mMaxFreq,
										cutoff,
										FftPowerOneAcquisitionSpectrogramChart.this);

					}
				});

				prevDayButton.setText("<< Prev. Acquisition");
				commands.setWidget(0, 0, prevDayButton);

			}

			// Attach button for panning within the acquisition

			if (leftBound > 0) {
				Button panLeftButton = new Button();
				panLeftButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						if (leftBound - window >= 0) {
							leftBound = (int) (leftBound - window);
							rightBound = rightBound + window;
						} else {
							rightBound = rightBound + leftBound;
							leftBound = 0;
						}
						help.setText(COMPUTING_PLEASE_WAIT);
						mSpectrumBrowser
								.getSpectrumBrowserService()
								.generateSingleAcquisitionSpectrogramAndOccupancy( mSensorId,
										mSelectionTime,
										mSys2detect,
										mMinFreq,
										mMaxFreq,
										(int) leftBound,
										(int) rightBound,
										cutoff,
										FftPowerOneAcquisitionSpectrogramChart.this);
					}
				});
				panLeftButton.setText("< Pan Left");
				panLeftButton.setTitle("Click to pan left");
				commands.setWidget(0, 1, panLeftButton);
			}

			// Attach the labels for the spectrogram power
			VerticalPanel powerLevelPanel = new VerticalPanel();
			powerLevelPanel.setWidth(100 + "px");
			this.maxPowerLabel = new Label();
			this.minPowerLabel = new Label();
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			powerLevelPanel.add(maxPowerLabel);
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			powerLevelPanel.add(new Label("Power (dBm) "));
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
			powerLevelPanel.add(minPowerLabel);
			// Attach labels for the frequency.
			freqPanel = new VerticalPanel();
			freqPanel.setWidth(100 + "px");
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			freqPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			freqPanel.add(new Label(Double.toString(maxFreqMhz)));
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			freqPanel.add(new Label("Frequency (MHz)"));
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
			freqPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			freqPanel.add(new Label(Double.toString(minFreqMhz)));
			powerMapPanel = new HorizontalPanel();
			powerMapPanel.setWidth(30 + "px");
			hpanel.add(freqPanel);
			spectrogramPanel = new VerticalPanel();

			HorizontalPanel spectrogramAndPowerMapPanel = new HorizontalPanel();
			spectrogramAndPowerMapPanel.add(spectrogramPanel);
			spectrogramAndPowerMapPanel.add(powerMapPanel);
			hpanel.add(spectrogramAndPowerMapPanel);
			currentValue = new Label(
					"Click for power spectrum and power at selected time. Double click to zoom.");
			tab1Panel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			tab1Panel.add(commands);
			if (maxTime - minTime < acquisitionDuration) {
				Button unzoom = new Button("Zoom Out");

				unzoom.addClickHandler(new ClickHandler() {
					@Override
					public void onClick(ClickEvent event) {
						zoomOut();
					}
				});
				commands.setWidget(0, 2, unzoom);
			}
			tab1Panel.add(currentValue);
			tab1Panel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			tab1Panel.add(hpanel);
			String helpString = "Single click for power spectrum. Double click to zoom.";

			// Add the slider bar for min occupancy selection.
			occupancyMinPowerVpanel = new VerticalPanel();
			occupancyMinPowerVpanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			occupancyMinPowerVpanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);

			occupancyMinPowerSliderBar = new SliderBarSimpleVertical(100,
					canvasPixelHeight + "px", true);
			occupancyMinPowerVpanel.add(occupancyMinPowerSliderBar);
			occupancyMinPowerSliderBar.setMaxValue(100);

			this.occupancyMinPowerLabel = new Label();
			occupancyMinPowerVpanel.add(occupancyMinPowerLabel);
			final Button cutoffAndRedrawButton = new Button("Cutoff and Redraw");
			commands.setWidget(0, 3, cutoffAndRedrawButton);
			cutoffAndRedrawButton.addClickHandler(new ClickHandler() {
				@Override
				public void onClick(ClickEvent event) {
					cutoffAndRedrawButton.setEnabled(false);
					help.setText(COMPUTING_PLEASE_WAIT);
					mSpectrumBrowser
							.getSpectrumBrowserService()
							.generateSingleAcquisitionSpectrogramAndOccupancy( mSensorId,
									mSelectionTime, mSys2detect, mMinFreq,
									mMaxFreq, leftBound, rightBound,
									cutoffPower,
									FftPowerOneAcquisitionSpectrogramChart.this);

				}
			});
			occupancyMinPowerSliderBar
					.addBarValueChangedHandler(new OccupancyMinPowerSliderHandler(
							occupancyMinPowerLabel));
			int initialValue = (int) ((double) (maxPower - cutoff)
					/ (double) (maxPower - minPower) * 100 );
			occupancyMinPowerSliderBar.setValue(initialValue);

			hpanel.add(occupancyMinPowerVpanel);

			spectrogramPanel.setTitle(helpString);
			spectrumAndOccupancyPanel = new VerticalPanel();
			spectrumAndOccupancyPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			tab1Panel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			tab1Panel.add(spectrumAndOccupancyPanel);
			

			occupancyPanel = new VerticalPanel();
			occupancyPanel.setWidth(canvasPixelWidth + "px");
			occupancyPanel.setHeight(canvasPixelHeight + "px");
			occupancyPanel.setPixelSize(canvasPixelWidth, canvasPixelHeight);
			// Fine pan to the right.
			if (rightBound > 0) {
				Button rightPanButton = new Button();
				rightPanButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						logger.finest("rightBound = " + rightBound + " leftBound = "
								+ leftBound + " window =  " + window + " aquisitionDuration = " + measurementsPerAcquisition);
						if (rightBound - window > 0) {
							rightBound = rightBound - window;
							leftBound = leftBound + window;
						} else {
							leftBound = leftBound + rightBound;
							rightBound = 0;
						}
						help.setText(COMPUTING_PLEASE_WAIT);
						mSpectrumBrowser
						.getSpectrumBrowserService()
						.generateSingleAcquisitionSpectrogramAndOccupancy(
								mSensorId,
								mSelectionTime,
								mSys2detect,
								mMinFreq,
								mMaxFreq,
								(int) leftBound,
								(int) rightBound,
								cutoff,
								FftPowerOneAcquisitionSpectrogramChart.this);
					}});
				commands.setWidget(0, 4, rightPanButton);
				rightPanButton.setTitle("Click to pan right");
				rightPanButton.setText("Pan Right >");
			}

			// Attach the next spectrogram panel.

			if (nextAcquisitionTime != mSelectionTime) {
				final Button nextAquisitionButton = new Button();
				nextAquisitionButton.setEnabled(true);
				nextAquisitionButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						logger.finer("getting next spectrogram");
						try {
							mSelectionTime = nextAcquisitionTime;
							nextAquisitionButton.setEnabled(false);
							acquisitionDuration = 0;
							leftBound = 0;
							rightBound = 0;
							window = measurementsPerAcquisition;
							help.setText(COMPUTING_PLEASE_WAIT);

							mSpectrumBrowser
									.getSpectrumBrowserService()
									.generateSingleAcquisitionSpectrogramAndOccupancy(
											mSensorId,
											nextAcquisitionTime,
											mSys2detect,
											mMinFreq,
											mMaxFreq,
											cutoff,
											FftPowerOneAcquisitionSpectrogramChart.this);
						} catch (Throwable th) {
							logger.log(Level.SEVERE,
									"Error calling spectrum browser service",
									th);
						}

					}
				});
				nextAquisitionButton.setText("Next Acquisition >>");
				// .setHTML("<img border='0' src='myicons/right-arrow.png' />");
				commands.setWidget(0, 5, nextAquisitionButton);
			}
			setSpectrogramImage();
			drawOccupancyChart();
			tabPanel = new TabPanel();
			tabPanel.add(tab1Panel, "[Spectrogram]");
			tabPanel.add(occupancyPanel, "[Occupancy]");
			tabPanel.selectTab(0);
			vpanel.add(tabPanel);
			tabPanel.addSelectionHandler(new SelectionHandler<Integer>() {

				@Override
				public void onSelection(SelectionEvent<Integer> event) {
					int item = event.getSelectedItem();
					if (item == 0) {
						help.setText("Single click for detail. Double click to zoom");
					} else if ( item == 1) {
						help.setText("Single click for spectrum");
					} else {
						help.setText("");
					}
				}});

		} catch (Throwable ex) {
			logger.log(Level.SEVERE, "Problem drawing specgtrogram", ex);
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error communicating with server", throwable);
		mSpectrumBrowser.displayError("Error communicating with server");
	}

}
