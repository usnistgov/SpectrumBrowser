package gov.nist.spectrumbrowser.client;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.canvas.client.Canvas;
import com.google.gwt.core.client.Duration;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.dom.client.ImageElement;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.ErrorEvent;
import com.google.gwt.event.dom.client.ErrorHandler;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.event.dom.client.MouseMoveEvent;
import com.google.gwt.event.dom.client.MouseMoveHandler;
import com.google.gwt.event.dom.client.MouseWheelEvent;
import com.google.gwt.event.dom.client.MouseWheelHandler;
import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
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
import com.google.gwt.user.client.ui.MenuBar;
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
import com.googlecode.gwt.charts.client.event.SelectEvent;
import com.googlecode.gwt.charts.client.event.SelectHandler;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.kiouri.sliderbar.client.event.BarValueChangedEvent;
import com.kiouri.sliderbar.client.event.BarValueChangedHandler;
import com.kiouri.sliderbar.client.solution.simplevertical.SliderBarSimpleVertical;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class FftPowerOneAcquisitionSpectrogramChart implements
		SpectrumBrowserCallback<String> {

	public static final String LABEL = "Acquisition Stats";
	String mSensorId;
	SpectrumBrowser mSpectrumBrowser;
	long mSelectionTime;
	SpectrumBrowserShowDatasets mSpectrumBrowserShowDatasets;
	DailyStatsChart mDailyStatsChart;
	OneDayOccupancyChart mOneDayOccupancyChart;
	JSONValue jsonValue;
	public static final long MILISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
	public long currentTime;
	public long currentFreq;
	private VerticalPanel spectrumAndOccupancyPanel;
	int cutoff;
	int maxPower;
	int cutoffPower;
	Label currentValue = new Label(
			"Click on spectrogram for power spectrum. Double click to zoom.");
	HorizontalPanel hpanel; // = new HorizontalPanel();
	VerticalPanel vpanel;// = new VerticalPanel();
	double minTime;
	double maxTime;
	long minFreq;
	long maxFreq;
	double timeDelta;
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
	private FitImage powerMapImage;
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
	private ArrayList<Integer> occupancyArray;
	private ScatterChart occupancyChart;
	private TabPanel tabPanel;
	private Image pleaseWaitImage;
	private int zoom = 2;
	private double acquisitionDuration = 0;
	private int window;
	private int leftBound;
	private int rightBound;
	private Timer timer;
	private Grid  commands;


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
			currentFreq = (long) ((maxFreq - minFreq) * yratio) + minFreq;
			currentTime = (long) (((double) ((maxTime - minTime) * xratio) + minTime) * 1000);
			currentValue.setText("Time (ms) since acquistion start = "
					+ currentTime + "; Freq = " + currentFreq + " MHz");
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
						* (maxPower - minPower) + minPower);
				occupancyMinPowerLabel.setText(Integer
						.toString((int) cutoffPower) + " dBm");

			} catch (Exception ex) {
				logger.log(Level.SEVERE, " Exception ", ex);
			}

		}

	}

	public FftPowerOneAcquisitionSpectrogramChart(String sensorId,
			long selectionTime, VerticalPanel verticalPanel,
			SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			DailyStatsChart dailyStatsChart,
			OneDayOccupancyChart oneDayOccupancyChart, int width, int height) {
		mSensorId = sensorId;
		mSelectionTime = selectionTime;
		vpanel = verticalPanel;
		mSpectrumBrowser = spectrumBrowser;
		mSpectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		mDailyStatsChart = dailyStatsChart;
		mOneDayOccupancyChart = oneDayOccupancyChart;

		ImagePreloader.load(SpectrumBrowser.getIconsPath()
				+ "computing-spectrogram-please-wait.png", null);
		pleaseWaitImage = new Image();
		vpanel.add(pleaseWaitImage);

		mSpectrumBrowser.getSpectrumBrowserService()
				.generateSingleAcquisitionSpectrogramAndOccupancy(
						mSpectrumBrowser.getSessionId(), sensorId,
						mSelectionTime, this);

	}

	@Override
	public void onSuccess(String result) {
		try {

			Duration duration = new Duration();
			// logger.finer("result = " + result);
			jsonValue = JSONParser.parseLenient(result);
			timeDelta = jsonValue.isObject().get("timeDelta").isNumber()
					.doubleValue();
			if (acquisitionDuration == 0) {
				acquisitionDuration = timeDelta;
				window = (int) timeDelta * 1000;
			}
			String spectrogramFile = jsonValue.isObject().get("spectrogram")
					.isString().stringValue();
			canvasPixelWidth = (int) jsonValue.isObject().get("image_width")
					.isNumber().doubleValue();
			canvasPixelHeight = (int) jsonValue.isObject().get("image_height")
					.isNumber().doubleValue();
			String colorBarFile = jsonValue.isObject().get("cbar").isString()
					.stringValue();
			spectrogramUrl = SpectrumBrowser.getGeneratedDataPath()
					+ spectrogramFile;
			cmapUrl = SpectrumBrowser.getGeneratedDataPath() + colorBarFile;
			maxPower = (int) jsonValue.isObject().get("maxPower").isNumber()
					.doubleValue();
			cutoff = (int) jsonValue.isObject().get("cutoff").isNumber()
					.doubleValue();
			minPower = (int) jsonValue.isObject().get("minPower").isNumber()
					.doubleValue();
			minFreq = (int) jsonValue.isObject().get("minFreq").isNumber()
					.doubleValue() / 1000000;
			maxFreq = (int) jsonValue.isObject().get("maxFreq").isNumber()
					.doubleValue() / 1000000;
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
			maxTime = minTime + timeDelta;
			timeArray = new ArrayList<Integer>();
			occupancyArray = new ArrayList<Integer>();
			int nvalues = jsonValue.isObject().get("timeArray").isArray()
					.size();
			for (int i = 0; i < nvalues; i++) {
				timeArray.add((int) jsonValue.isObject().get("timeArray")
						.isArray().get(i).isNumber().doubleValue());
				occupancyArray.add((int) jsonValue.isObject()
						.get("occupancyArray").isArray().get(i).isNumber()
						.doubleValue());
			}
			long elapsedTime = duration.elapsedMillis();
			logger.finer("Unpacking json object took " + elapsedTime);

		} catch (Throwable throwable) {
			logger.log(Level.SEVERE, "Error parsing json result from server",
					throwable);
			mSpectrumBrowser.displayError("Error parsing JSON");
		}
		draw();

	}

	private void drawNavigation() {
		MenuBar menuBar = new MenuBar();
		SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();

		menuBar.addItem(safeHtml.appendEscaped(SpectrumBrowser.LOGOFF_LABEL)
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				mSpectrumBrowser.logoff();

			}
		});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(
						SpectrumBrowserShowDatasets.LABEL).toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						mSpectrumBrowserShowDatasets.buildUi();
					}
				});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(DailyStatsChart.LABEL)
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						mDailyStatsChart.draw();
					}
				});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(
						OneDayOccupancyChart.END_LABEL).toSafeHtml(),
				new Scheduler.ScheduledCommand() {
					@Override
					public void execute() {
						mOneDayOccupancyChart.draw();

					}
				});

		menuBar.addItem(
				new SafeHtmlBuilder()
						.appendEscaped(SpectrumBrowser.ABOUT_LABEL)
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {

					}
				});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(SpectrumBrowser.HELP_LABEL)
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						// TODO Auto-generated method stub

					}
				});
		vpanel.add(menuBar);

	}
	
	private void zoomIn() {

		leftBound = (int) (minTime * 1000 + (currentTime - minTime * 1000)
				/ (double) zoom);
		rightBound = (int) ((acquisitionDuration * 1000 - maxTime * 1000) 
				+ (maxTime * 1000 - currentTime) / (double) zoom);
		window = (int) acquisitionDuration * 1000 - leftBound
				- rightBound;
		logger.finer("mintTime " + minTime + " maxTime " + maxTime
				+ " currentTime " + currentTime + " leftBound "
				+ leftBound + " rightBound " + rightBound);
		if (window < 50) {
			logger.finer("Max zoom reached " + window);
			return;
		}
		vpanel.clear();
		mSpectrumBrowser
				.getSpectrumBrowserService()
				.generateSingleAcquisitionSpectrogramAndOccupancy(
						mSpectrumBrowser.getSessionId(), mSensorId,
						mSelectionTime, (int) leftBound,
						(int) rightBound, cutoff,
						FftPowerOneAcquisitionSpectrogramChart.this);
	}
	
	private void zoomOut() {
		if (maxTime - minTime < acquisitionDuration) {
			vpanel.clear();
			mSpectrumBrowser
					.getSpectrumBrowserService()
					.generateSingleAcquisitionSpectrogramAndOccupancy(
							mSpectrumBrowser.getSessionId(),
							mSensorId,
							mSelectionTime,
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
		

	

		spectrogramCanvas.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				if ( timer == null) {
					timer = new Timer() {
						@Override
						public void run() {
							logger.finer("OneAcquisitionSpegrogramChart: clickHandler");
							if (currentFreq <= 0) {
								logger.finer("Freq is 0 -- doing nothing");
								return;
							}
							VerticalPanel powerVsTimeHpanel = new VerticalPanel();
								
							new PowerVsTime(mSpectrumBrowser, powerVsTimeHpanel, mSensorId,
									mSelectionTime, currentFreq, canvasPixelWidth, canvasPixelHeight,
									leftBound,rightBound);
							new PowerSpectrum(mSpectrumBrowser, powerVsTimeHpanel,
									mSensorId, mSelectionTime, currentTime,
									canvasPixelWidth, canvasPixelHeight);
							tabPanel.add(powerVsTimeHpanel, Long.toString(currentTime)
									+ " ms");
						}};
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
				/ (double) (maxFreq - minFreq);
		logger.finer("yPixelsPerMegaherz = " + yPixelsPerMegahertz
				+ "canvasPixelHeight " + canvasPixelHeight);

		if (cmapUrl != null) {
			ImagePreloader.load(cmapUrl, new ImageLoadHandler() {

				@Override
				public void imageLoaded(ImageLoadEvent event) {
					FitImage image = new FitImage();
					// TODO -- make this width part of CSS
					image.setFixedWidth(30);
					image.setHeight(canvasPixelHeight + "px");
					image.setUrl(event.getImageUrl());
					image.setPixelSize(30, canvasPixelHeight);
					ImageElement imageElement = ImageElement.as(image
							.getElement());
					imageElement.setAttribute("HEIGHT", canvasPixelHeight
							+ "px");

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

			spectrogramImage = new FitImage();
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
					logger.log(Level.SEVERE, "Error loading image");
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
		dataTable.addColumn(ColumnType.NUMBER,
				" Time since start acquisition (ms).");
		dataTable.addColumn(ColumnType.NUMBER, " Occupancy %");
		dataTable.addRows(timeArray.size());
		for (int i = 0; i < timeArray.size(); i++) {
			dataTable.setValue(i, 0, (double) timeArray.get(i));
			dataTable.setValue(i, 1, (double) occupancyArray.get(i));
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
				options.setHAxis(HAxis
						.create("Miliseconds Since Start of Aquisition"));
				options.setVAxis(VAxis.create("Band Occupancy %"));
				occupancyChart.setStyleName("lineChart");
				occupancyChart.draw(dataTable, options);
				occupancyChart.setVisible(true);
				occupancyPanel.add(occupancyChart);
				occupancyChart.addSelectHandler(new SelectHandler() {

					@Override
					public void onSelect(SelectEvent event) {
						JsArray<Selection> selection = occupancyChart
								.getSelection();
						int row = selection.get(0).getRow();
						currentTime = timeArray.get(row);
						logger.finer("OneAcquisitionSpegrogramChart: clickHandler");
						VerticalPanel spectrumHpanel = new VerticalPanel();
						new PowerSpectrum(mSpectrumBrowser, spectrumHpanel,
								mSensorId, mSelectionTime, currentTime,
								canvasPixelWidth, canvasPixelHeight);
						tabPanel.add(spectrumHpanel, Long.toString(currentTime)
								+ " ms");

					}
				});

			}
		});

	}

	private void draw() {
		try {
			vpanel.clear();

			drawNavigation();
			HTML title = new HTML("<H2>Acquisition Start Time : " + localDateOfAcquisition
					+ "; Occupancy Threshold : " + cutoff
					+ " dBm; Noise Floor : " + noiseFloor + "dBm.</H2>");
			vpanel.add(title);

			VerticalPanel tab1Panel = new VerticalPanel();

			hpanel = new HorizontalPanel();
			
			commands = new Grid(1,4);
			commands.setStyleName("selectionGrid");

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
			xaxis.add(new Label("Time (seconds)"));
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
						vpanel.clear();
						vpanel.add(pleaseWaitImage);
						mSpectrumBrowser
								.getSpectrumBrowserService()
								.generateSingleAcquisitionSpectrogramAndOccupancy(
										mSpectrumBrowser.getSessionId(),
										mSensorId,
										prevAcquisitionTime,
										cutoff,
										FftPowerOneAcquisitionSpectrogramChart.this);

					}
				});

				prevDayButton
						.setHTML("<img border='0' src='myicons/left-arrow.png' />");
				
				commands.setWidget(0,0,prevDayButton);
				
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
			freqPanel.add(new Label(Long.toString(maxFreq)));
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			freqPanel.add(new Label("Frequency (MHz)"));
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
			freqPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			freqPanel.add(new Label(Long.toString(minFreq)));
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
			Button unzoom = new Button("Zoom Out");
		
			unzoom.addClickHandler(new ClickHandler(){
				@Override
				public void onClick(ClickEvent event) {
					zoomOut();
				}});
			commands.setWidget(0,1,unzoom);
			tab1Panel.add(currentValue);
			tab1Panel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			tab1Panel.add(hpanel);
			String helpString = "Single click for power spectrum. Mouse wheel or double click to zoom.";

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
			final Button cutoffAndRedrawButton = new Button(
					"Cutoff and Redraw");
			commands.setWidget(0,2,cutoffAndRedrawButton);
			cutoffAndRedrawButton.addClickHandler(new ClickHandler() {
				@Override
				public void onClick(ClickEvent event) {
					cutoffAndRedrawButton.setEnabled(false);
					mSpectrumBrowser
							.getSpectrumBrowserService()
							.generateSingleAcquisitionSpectrogramAndOccupancy(
									mSpectrumBrowser.getSessionId(), mSensorId,
									mSelectionTime, leftBound, rightBound, cutoffPower,
									FftPowerOneAcquisitionSpectrogramChart.this);

				}
			});
			occupancyMinPowerSliderBar
					.addBarValueChangedHandler(new OccupancyMinPowerSliderHandler(
							occupancyMinPowerLabel));
			int initialValue =(int)( (double)(maxPower - cutoff)/(double)(maxPower - minPower)*100);
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

			// Attach the next spectrogram panel.
			if (nextAcquisitionTime != mSelectionTime) {
				VerticalPanel nextSpectrogramPanel = new VerticalPanel();
				nextSpectrogramPanel
						.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
				final Button nextDayButton = new Button();
				nextDayButton.setEnabled(true);
				nextDayButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						logger.finer("getting next spectrogram");
						try {
							mSelectionTime = nextAcquisitionTime;
							nextDayButton.setEnabled(false);
							mSpectrumBrowser
									.getSpectrumBrowserService()
									.generateSingleAcquisitionSpectrogramAndOccupancy(
											mSpectrumBrowser.getSessionId(),
											mSensorId,
											nextAcquisitionTime,
											cutoff,
											FftPowerOneAcquisitionSpectrogramChart.this);
						} catch (Throwable th) {
							logger.log(Level.SEVERE,
									"Error calling spectrum browser service",
									th);
						}

					}
				});
				nextDayButton
						.setHTML("<img border='0' src='myicons/right-arrow.png' />");
				commands.setWidget(0,3,nextDayButton);

				hpanel.add(nextSpectrogramPanel);

			}
			setSpectrogramImage();
			drawOccupancyChart();
			tabPanel = new TabPanel();
			tabPanel.add(tab1Panel, "[Spectrogram]");
			tabPanel.add(occupancyPanel, "[Occupancy]");
			tabPanel.selectTab(0);
			vpanel.add(tabPanel);

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
