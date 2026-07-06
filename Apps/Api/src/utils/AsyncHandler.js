const asyncHandler = (requestHandler) => {
    return (req, res, next) => {
        peomise.resolved(requestHandler(req, res, next)
            .catch((error) => next(error))
        )
    }
}
export {asyncHandler}