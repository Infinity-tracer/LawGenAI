-- NyayAssist MySQL Database Schema
-- Complete database for Legal AI Assistant

CREATE DATABASE IF NOT EXISTS nyayassist_db;
USE nyayassist_db;

-- =====================================================
-- 1. USERS TABLE - Complete user data
-- =====================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_uuid VARCHAR(36) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    profile_picture_url VARCHAR(500),
    role ENUM('user', 'admin', 'moderator') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_user_uuid (user_uuid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. ACCESS LOGS TABLE - Track all API access
-- =====================================================
CREATE TABLE access_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    user_uuid VARCHAR(36) NULL,
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    request_body JSON,
    response_status_code INT,
    response_time_ms INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_endpoint (endpoint),
    INDEX idx_created_at (created_at),
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. CHAT SESSIONS TABLE - Store chat sessions
-- =====================================================
CREATE TABLE chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id INT NULL,
    title VARCHAR(255) DEFAULT 'New Chat',
    chat_mode ENUM('PDF_CHAT', 'KANOON_SEARCH') NOT NULL,
    folder VARCHAR(100),
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_uuid (session_uuid),
    INDEX idx_chat_mode (chat_mode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 4. MESSAGES TABLE - Store all chat messages
-- =====================================================
CREATE TABLE messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message_uuid VARCHAR(36) UNIQUE NOT NULL,
    session_id INT NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content LONGTEXT NOT NULL,
    message_type ENUM('text', 'cases', 'error', 'system') DEFAULT 'text',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_message_uuid (message_uuid),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 5. LLM OUTPUTS TABLE - Store all LLM/Gemini responses
-- =====================================================
CREATE TABLE llm_outputs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    output_uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id INT NULL,
    session_id INT NULL,
    message_id BIGINT NULL,
    
    -- Request details
    model_name VARCHAR(100) DEFAULT 'gemini-2.5-flash',
    prompt_template TEXT,
    context_provided LONGTEXT,
    user_question TEXT NOT NULL,
    
    -- Response details
    llm_response LONGTEXT NOT NULL,
    tokens_used INT,
    response_time_ms INT,
    temperature DECIMAL(3,2) DEFAULT 0.30,
    
    -- Status and metadata
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_model_name (model_name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 6. KANOON QUERIES TABLE - Store Indian Kanoon searches
-- =====================================================
CREATE TABLE kanoon_queries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    query_uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id INT NULL,
    session_id INT NULL,
    message_id BIGINT NULL,
    
    -- Query details
    search_query TEXT NOT NULL,
    page_number INT DEFAULT 0,
    
    -- Response details
    total_results_found INT DEFAULT 0,
    results_returned INT DEFAULT 0,
    response_time_ms INT,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    raw_api_response JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    FULLTEXT INDEX idx_search_query (search_query)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 7. KANOON CASE RESULTS TABLE - Store individual case results
-- =====================================================
CREATE TABLE kanoon_case_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    query_id BIGINT NOT NULL,
    doc_id VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    snippet TEXT,
    case_link VARCHAR(500),
    headline TEXT,
    result_rank INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (query_id) REFERENCES kanoon_queries(id) ON DELETE CASCADE,
    INDEX idx_query_id (query_id),
    INDEX idx_doc_id (doc_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 8. PDF UPLOADS TABLE - Track uploaded PDFs
-- =====================================================
CREATE TABLE pdf_uploads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id INT NULL,
    session_id INT NULL,
    
    -- File details
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),  -- SHA-256 hash for deduplication
    mime_type VARCHAR(100) DEFAULT 'application/pdf',
    
    -- Processing details
    pages_count INT,
    text_extracted LONGTEXT,
    chunks_processed INT DEFAULT 0,
    chunk_size INT DEFAULT 10000,
    chunk_overlap INT DEFAULT 1000,
    
    -- Vector store info
    faiss_index_path VARCHAR(500),
    embedding_model VARCHAR(100) DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
    
    -- Status
    processing_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_upload_uuid (upload_uuid),
    INDEX idx_file_hash (file_hash),
    INDEX idx_processing_status (processing_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 9. PDF TEXT CHUNKS TABLE - Store individual text chunks
-- =====================================================
CREATE TABLE pdf_text_chunks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    upload_id INT NOT NULL,
    chunk_index INT NOT NULL,
    chunk_text LONGTEXT NOT NULL,
    chunk_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (upload_id) REFERENCES pdf_uploads(id) ON DELETE CASCADE,
    INDEX idx_upload_id (upload_id),
    UNIQUE KEY uk_upload_chunk (upload_id, chunk_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 10. USER SESSIONS TABLE - Track login sessions
-- =====================================================
CREATE TABLE user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_token (session_token),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 11. API RATE LIMITS TABLE - Track rate limiting
-- =====================================================
CREATE TABLE api_rate_limits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    ip_address VARCHAR(45),
    endpoint VARCHAR(255) NOT NULL,
    request_count INT DEFAULT 1,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_ip_address (ip_address),
    INDEX idx_window_end (window_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 12. ANALYTICS TABLE - Aggregate analytics data
-- =====================================================
CREATE TABLE analytics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    metric_type ENUM('daily_users', 'daily_queries', 'pdf_uploads', 'kanoon_searches', 'llm_calls') NOT NULL,
    metric_value INT DEFAULT 0,
    additional_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_date_metric (date, metric_type),
    INDEX idx_date (date),
    INDEX idx_metric_type (metric_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 13. FEEDBACK TABLE - User feedback and ratings
-- =====================================================
CREATE TABLE feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    feedback_uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id INT NULL,
    message_id BIGINT NULL,
    llm_output_id BIGINT NULL,
    kanoon_query_id BIGINT NULL,
    
    rating INT CHECK (rating >= 1 AND rating <= 5),
    feedback_type ENUM('helpful', 'not_helpful', 'incorrect', 'offensive', 'other') NOT NULL,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (llm_output_id) REFERENCES llm_outputs(id) ON DELETE SET NULL,
    FOREIGN KEY (kanoon_query_id) REFERENCES kanoon_queries(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View: User activity summary
CREATE OR REPLACE VIEW vw_user_activity AS
SELECT 
    u.id as user_id,
    u.full_name,
    u.email,
    COUNT(DISTINCT cs.id) as total_sessions,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT lo.id) as total_llm_calls,
    COUNT(DISTINCT kq.id) as total_kanoon_searches,
    COUNT(DISTINCT pu.id) as total_pdf_uploads,
    u.last_login_at,
    u.created_at as registered_at
FROM users u
LEFT JOIN chat_sessions cs ON u.id = cs.user_id
LEFT JOIN messages m ON cs.id = m.session_id
LEFT JOIN llm_outputs lo ON u.id = lo.user_id
LEFT JOIN kanoon_queries kq ON u.id = kq.user_id
LEFT JOIN pdf_uploads pu ON u.id = pu.user_id
GROUP BY u.id;

-- View: Daily usage statistics
CREATE OR REPLACE VIEW vw_daily_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_requests,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(response_time_ms) as avg_response_time_ms
FROM access_logs
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- View: Popular Kanoon searches
CREATE OR REPLACE VIEW vw_popular_kanoon_searches AS
SELECT 
    search_query,
    COUNT(*) as search_count,
    AVG(total_results_found) as avg_results,
    MAX(created_at) as last_searched
FROM kanoon_queries
WHERE success = TRUE
GROUP BY search_query
ORDER BY search_count DESC;

-- =====================================================
-- STORED PROCEDURES
-- =====================================================

DELIMITER //

-- Procedure: Log API access
CREATE PROCEDURE sp_log_access(
    IN p_user_id INT,
    IN p_user_uuid VARCHAR(36),
    IN p_session_id VARCHAR(100),
    IN p_ip_address VARCHAR(45),
    IN p_user_agent TEXT,
    IN p_endpoint VARCHAR(255),
    IN p_http_method VARCHAR(10),
    IN p_request_body JSON,
    IN p_response_status_code INT,
    IN p_response_time_ms INT,
    IN p_error_message TEXT
)
BEGIN
    INSERT INTO access_logs (
        user_id, user_uuid, session_id, ip_address, user_agent,
        endpoint, http_method, request_body, response_status_code,
        response_time_ms, error_message
    ) VALUES (
        p_user_id, p_user_uuid, p_session_id, p_ip_address, p_user_agent,
        p_endpoint, p_http_method, p_request_body, p_response_status_code,
        p_response_time_ms, p_error_message
    );
END //

-- Procedure: Log LLM output
CREATE PROCEDURE sp_log_llm_output(
    IN p_output_uuid VARCHAR(36),
    IN p_user_id INT,
    IN p_session_id INT,
    IN p_message_id BIGINT,
    IN p_model_name VARCHAR(100),
    IN p_prompt_template TEXT,
    IN p_context_provided LONGTEXT,
    IN p_user_question TEXT,
    IN p_llm_response LONGTEXT,
    IN p_tokens_used INT,
    IN p_response_time_ms INT,
    IN p_temperature DECIMAL(3,2),
    IN p_success BOOLEAN,
    IN p_error_message TEXT
)
BEGIN
    INSERT INTO llm_outputs (
        output_uuid, user_id, session_id, message_id, model_name,
        prompt_template, context_provided, user_question, llm_response,
        tokens_used, response_time_ms, temperature, success, error_message
    ) VALUES (
        p_output_uuid, p_user_id, p_session_id, p_message_id, p_model_name,
        p_prompt_template, p_context_provided, p_user_question, p_llm_response,
        p_tokens_used, p_response_time_ms, p_temperature, p_success, p_error_message
    );
END //

-- Procedure: Log Kanoon query
CREATE PROCEDURE sp_log_kanoon_query(
    IN p_query_uuid VARCHAR(36),
    IN p_user_id INT,
    IN p_session_id INT,
    IN p_message_id BIGINT,
    IN p_search_query TEXT,
    IN p_page_number INT,
    IN p_total_results_found INT,
    IN p_results_returned INT,
    IN p_response_time_ms INT,
    IN p_success BOOLEAN,
    IN p_error_message TEXT,
    IN p_raw_api_response JSON
)
BEGIN
    INSERT INTO kanoon_queries (
        query_uuid, user_id, session_id, message_id, search_query,
        page_number, total_results_found, results_returned, response_time_ms,
        success, error_message, raw_api_response
    ) VALUES (
        p_query_uuid, p_user_id, p_session_id, p_message_id, p_search_query,
        p_page_number, p_total_results_found, p_results_returned, p_response_time_ms,
        p_success, p_error_message, p_raw_api_response
    );
END //

-- Procedure: Clean old access logs (keep last 90 days)
CREATE PROCEDURE sp_cleanup_old_logs()
BEGIN
    DELETE FROM access_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
    DELETE FROM api_rate_limits WHERE window_end < NOW();
END //

DELIMITER ;

-- =====================================================
-- TRIGGERS
-- =====================================================

DELIMITER //

-- Trigger: Update analytics on new LLM output
CREATE TRIGGER trg_llm_output_analytics
AFTER INSERT ON llm_outputs
FOR EACH ROW
BEGIN
    INSERT INTO analytics (date, metric_type, metric_value)
    VALUES (DATE(NEW.created_at), 'llm_calls', 1)
    ON DUPLICATE KEY UPDATE metric_value = metric_value + 1;
END //

-- Trigger: Update analytics on new Kanoon query
CREATE TRIGGER trg_kanoon_query_analytics
AFTER INSERT ON kanoon_queries
FOR EACH ROW
BEGIN
    INSERT INTO analytics (date, metric_type, metric_value)
    VALUES (DATE(NEW.created_at), 'kanoon_searches', 1)
    ON DUPLICATE KEY UPDATE metric_value = metric_value + 1;
END //

-- Trigger: Update analytics on PDF upload
CREATE TRIGGER trg_pdf_upload_analytics
AFTER INSERT ON pdf_uploads
FOR EACH ROW
BEGIN
    INSERT INTO analytics (date, metric_type, metric_value)
    VALUES (DATE(NEW.created_at), 'pdf_uploads', 1)
    ON DUPLICATE KEY UPDATE metric_value = metric_value + 1;
END //

DELIMITER ;

-- =====================================================
-- SAMPLE DATA (Optional - for testing)
-- =====================================================

-- Insert sample admin user (password: admin123 - hashed)
-- INSERT INTO users (user_uuid, full_name, email, phone, password_hash, role, is_verified)
-- VALUES (UUID(), 'Admin User', 'admin@nyayassist.com', '+91-9999999999', 
--         '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4lP5uMwkXEBOt/oW', 'admin', TRUE);

SELECT 'NyayAssist Database Schema Created Successfully!' AS Status;
