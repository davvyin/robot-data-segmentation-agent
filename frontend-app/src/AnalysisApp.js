import React, { useState, useRef } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import {
    Button,
    Input,
    Box,
    Text,
    VStack,
    Heading,
    useToast,
    Skeleton,
    Alert,
    AlertIcon,
    Divider,
    Spinner,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td
} from '@chakra-ui/react';

const SOCKET_URL = 'http://0.0.0.0:8080';

const AnalysisApp = () => {
    const [videoUrl, setVideoUrl] = useState('');
    const [file, setFile] = useState(null);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [jobId, setJobId] = useState('');
    const [socket, setSocket] = useState(null);
    const [videoSrc, setVideoSrc] = useState('');
    const [stages, setStages] = useState({});
    const [step, setStep] = useState(0); // step 0 or 1
    const [showSkeleton, setShowSkeleton] = useState(false);
    const fileInputRef = useRef(null);
    const toast = useToast();

    const handleUpload = async () => {
        setLoading(true);
        setShowSkeleton(true);
        setStages({});

        if (!file && !videoUrl) {
            toast({
                title: 'Upload Error',
                description: 'No video file or URL provided.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
            setLoading(false);
            return;
        }

        const socketInstance = io(SOCKET_URL, {
            reconnectionAttempts: 3,
            timeout: 5000,
            transports: ["websocket"]
        });

        setSocket(socketInstance);

        socketInstance.on('connect', async () => {
            console.log("Connected with SID: ", socketInstance.id);

            socketInstance.emit('subscribe', { sid: socketInstance.id });

            const formData = new FormData();
            formData.append('sid', socketInstance.id);

            if (file) {
                formData.append('video', file);
                setVideoSrc(URL.createObjectURL(file));
            } else if (videoUrl) {
                formData.append('videoUrl', videoUrl);
                setVideoSrc(videoUrl);
            }

            try {
                const response = await axios.post('http://0.0.0.0:8080/run_job', formData);
                const { job_id } = response.data;
                setJobId(job_id);

                toast({
                    title: 'Upload success',
                    description: "We've received your video and started processing.",
                    status: 'success',
                    duration: 5000,
                    isClosable: true,
                });
                setStep(2);
            } catch (error) {
                toast({
                    title: 'Upload Error',
                    description: error.message,
                    status: 'error',
                    duration: 5000,
                    isClosable: true,
                });
            }
        });

        socketInstance.on('job_update', (data) => {
            console.log("Job Update Received:", data);
            setStages((prev) => ({
                ...prev,
                [data.stage]: data.status,
            }));
        });

        socketInstance.on('job_done', (data) => {
            console.log("Job Completed:", data.job_id);
            toast({
                title: 'Job Completed',
                description: `Job ${data.job_id} has finished.`,
                status: 'success',
                duration: 5000,
                isClosable: true,
            });
            setAnalysisResult(data.result);
            setShowSkeleton(false);
            setLoading(false);
        });

        socketInstance.on('job_error', (data) => {
            console.log("Job Failed:", data.error);
            toast({
                title: 'Job Failed',
                description: data.error,
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
            setShowSkeleton(false);
            setLoading(false);
        });

        setLoading(false);
    };

    const renderStages = () => (
        <VStack align="start" spacing={2}>
            {Object.entries(stages).map(([key, value]) => (
                <Box key={key} p={2} w="100%">
                    <Text>
                        <strong>{key.replace('_', ' ').toUpperCase()}:</strong> {value}
                    </Text>
                    {value === "processing" && <Spinner size="sm" />}
                </Box>
            ))}
        </VStack>
    );

    const renderResults = () => (
        <>
            <Box mt="4">
                <Heading size="sm">Raw JSON Data:</Heading>
                <pre style={{ background: '#f7f7f7', padding: '10px', borderRadius: '5px' }}>
                    {JSON.stringify(analysisResult, null, 2)}
                </pre>
            </Box>
        </>
    );

    return (
        <Box maxW="700px" mx="auto" mt="10">

            <VStack spacing="4">
                <Heading>AI Video Analysis</Heading>

                {step === 0 && (
                    <Box>
                        <Text>Step 1: Please upload video or provide URL</Text>
                        <Input
                            placeholder="Enter Video URL"
                            value={videoUrl}
                            onChange={(e) => {
                                setVideoUrl(e.target.value);
                                setFile(null); 
                                setVideoSrc(e.target.value);
                                if (fileInputRef.current) {
                                    fileInputRef.current.value = ""; 
                                }
                            }}
                        />
                        <Heading> OR </Heading>
                        <Button mt="2" variant="outline" onClick={() => fileInputRef.current.click()}>
                            Select Video File
                        </Button>
                        <Input
                            type="file"
                            ref={fileInputRef}
                            display="none"
                            onChange={(e) => {
                                setFile(e.target.files[0]);
                                setVideoUrl(''); 
                                setVideoSrc(URL.createObjectURL(e.target.files[0]));
                            }}
                        />
                        {videoSrc && (
                            <Box mt="4">
                                <Text>Video Preview:</Text>
                                <video
                                    src={videoSrc}
                                    controls
                                    width="100%"
                                    height="auto"
                                />
                            </Box>
                        )}
                        <Button
                            mt="4"
                            colorScheme="teal"
                            isDisabled={
                                (!file && !videoUrl) ||
                                (file && !file.name.match(/\.(mp4)$/i)) ||
                                (videoUrl && !videoUrl.match(/^https?:\/\/.*\.(mp4)$/i))
                            }
                            onClick={() => { setStep(1); setAnalysisResult(null) }}
                        >
                            Next
                        </Button>
                    </Box>
                )}

                {step === 1 && (
                    <Box>
                        <Text>Step 2: Start Analysis</Text>
                        <Button
                            onClick={handleUpload}
                            colorScheme="teal"
                            isLoading={loading}
                        >
                            Upload and Start Analysis
                        </Button>
                        <Button
                            mt="2"
                            onClick={() => setStep(0)}
                        >
                            Go Back
                        </Button>
                    </Box>
                )}

                {step === 2 && (
                    <Box w="100%" mt="4">
                        <Text fontSize="lg">Current Stages:</Text>
                        {renderStages()}
                        {analysisResult && (
                            <Box mt="4">
                                <Text fontSize="lg" mb="2">Analysis Result:</Text>
                                {renderResults()}
                            </Box>
                        )}
                        <Button
                            mt="4"
                            colorScheme="teal"
                            isLoading={analysisResult == null}
                            onClick={() => setStep(0)}
                        >
                            Go Back
                        </Button>
                    </Box>
                )}
            </VStack>
        </Box>
    );
};

export default AnalysisApp;